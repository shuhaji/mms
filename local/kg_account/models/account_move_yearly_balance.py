from odoo import models, fields, api


class KGAccountMoveYearlyBalance(models.Model):
    _name = 'account.move.yearly.balance'
    _description = ' Account Move Yearly Balance'

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    period = fields.Integer('Period in Year', required=True)
    account_id = fields.Many2one('account.account', 'Account ID', required=True)
    state = fields.Char('State', size=10, required=True)
    is_must_recalc = fields.Boolean('Recalculation Boolean', default=False)
    balance = fields.Monetary(default=0.0, currency_field='company_currency_id')
    initial_balance = fields.Integer('Intial balance', default=0)
    company_currency_id = fields.Many2one('res.currency')

    @api.model_cr
    def init(self):
        self._cr.execute("select version()")
        db_version = self._cr.dictfetchall()
        if db_version and "PostgreSQL 9.4" not in db_version[0].get('version'):
            self.create_indexes()
            self.create_yearly_balance_dml()
        else:
            self.create_indexes_9_4()
        self.create_for_initial_balance_dml()

    def create_indexes(self):
        self._cr.execute("""
             create unique index if not exists account_move_yearly_balance_index 
                on account_move_yearly_balance
                using btree(company_id, period, account_id, state);
             create index if not exists account_move_yearly_balance_mat_recalc_index 
                on account_move_yearly_balance
                using btree(is_must_recalc);
             create index if not exists account_move_line_yearly_balance_index 
                on account_move_line
                using btree(company_id, date_part('year', date), account_id, move_id);
                """)

    def create_indexes_9_4(self):
        self._cr.execute("""
            DO
            $$
            BEGIN 
                IF to_regclass('account_move_yearly_balance_index') IS NULL THEN
                 create unique index account_move_yearly_balance_index 
                    on account_move_yearly_balance
                    using btree(company_id, period, account_id, state);
                end if;
                IF to_regclass('account_move_yearly_balance_mat_recalc_index') IS NULL THEN
                 create index account_move_yearly_balance_mat_recalc_index 
                    on account_move_yearly_balance
                    using btree(is_must_recalc);
                end if;
                IF to_regclass('account_move_line_yearly_balance_index') IS NULL THEN
                 create index account_move_line_yearly_balance_index 
                    on account_move_line
                    using btree(company_id, date_part('year', date), account_id, move_id);
                end if;
            END;
            $$;
                """)

    def create_yearly_balance_dml(self):
        # self._cr.execute(""" SELECT * FROM account_move_yearly_balance WHERE indexname = %s""",
        #                  ('account_move_yearly_balance',))
        # if not self._cr.fetchone():
        self._cr.execute("""                
            create or replace function account_move_line_yearly_balance_func_triggers() returns trigger
              -- security definer
              language plpgsql
            as $$
            declare 
                move_id int;
                new_state varchar;
                old_state varchar;
                existing_id int;
            begin
                IF (TG_OP = 'INSERT' or TG_OP = 'UPDATE') AND  date_part('year', new.date) < date_part('year', NOW()) then	
                    select m.id, m.state into move_id , new_state 
                    from account_move m where m.id = NEW.move_id;		
                
                    update account_move_yearly_balance t
                        set is_must_recalc = true
                            , balance = t.balance + (NEW.debit - NEW.credit)
                        where t.company_id = NEW.company_id 
                            and t.period = date_part('year', NEW.date)
                            and t.account_id = NEW.account_id
                            and t.state = new_state;
                        
                    insert into account_move_yearly_balance (
                            company_id, period, account_id, state, balance, is_must_recalc)
                    select NEW.company_id, date_part('year', NEW.date), NEW.account_id, 
                        coalesce(new_state, 'draft'), 
                        (NEW.debit - NEW.credit) as balance, true as is_must_recalc
                    on conflict (company_id, period, account_id, state)
                    do nothing;
                end if;
            
                if (TG_OP = 'UPDATE' or TG_OP = 'DELETE') AND date_part('year', OLD.date) < date_part('year', NOW()) then
                    select m.id, m.state into move_id , old_state
                    from account_move m where m.id = OLD.move_id;
                    
                    if (TG_OP = 'DELETE' or old_state != new_state or NEW.account_id != OLD.account_id 
                            or NEW.company_id != OLD.company_id 
                            or date_part('year', OLD.date) != date_part('year', NEW.date) 
                            or NEW.debit != OLD.debit
                            or NEW.credit != OLD.credit
                        ) then
                        update account_move_yearly_balance t
                            set is_must_recalc = true
                                , balance = t.balance - (OLD.debit - OLD.credit)
                            where  t.company_id = OLD.company_id
                                and t.period = date_part('year', OLD.date)
                                and t.account_id = OLD.account_id
                                and t.state = old_state;
                    end if;
                  
                 
                end if;
                
                IF (TG_OP = 'INSERT' or TG_OP = 'UPDATE') then	
                    return NEW;
                else
                    return OLD;
                end if;
            end;
            $$;
                
            drop trigger if exists account_move_line_yearly_balance_triggers on account_move_line;

            create trigger account_move_line_yearly_balance_triggers 
                after insert or update or delete 
                on account_move_line
                for each row execute procedure account_move_line_yearly_balance_func_triggers();
               
               
               
            create or replace function account_move_yearly_balance_func_triggers() returns trigger
              -- security definer
              language plpgsql
            as $$
            declare 
                existing_id int;
            begin
                IF (TG_OP = 'UPDATE') then	
                    if (NEW.state != OLD.state) then				
                        with z_summary_move as (
                            select aml.company_id, date_part('year', aml.date)::int as period, aml.account_id,  
                                sum(aml.debit - aml.credit) as balance, true as is_must_recalc, 
                                coalesce(NEW.state, 'draft')::varchar as new_state, coalesce(OLD.state, 'draft')::varchar as old_state
                                -- 'posted'::varchar as new_state, 'draft'::varchar as old_state
                                -- NEW.state as new_state, OLD.state as old_state
                                from account_move_line aml
                                where 
                                aml.move_id = NEW.id
                                -- aml.move_id in (4644, 4403, 4404, 4643)
                                and date_part('year', aml.date) < date_part('year', NOW())
                                group by aml.company_id, date_part('year', aml.date)::int, aml.account_id
                            )
                            -- select * from z_summary_move;			 				 	
                            , updated_new_state as (
                                update account_move_yearly_balance t
                                set is_must_recalc = true
                                    , balance = t.balance + coalesce(s.balance, 0)
                                from z_summary_move s
                                where s.company_id = t.company_id 
                                    and s.period = t.period
                                    and s.account_id = t.account_id
                                    and s.new_state = t.state
                                returning t.*, s.balance as new_balance
                            ) 
                            -- select * from account_move_yearly_balance s inner join updated_new_state t on t.id = s.id;
                            , inserted_new_state as (
                                insert into account_move_yearly_balance (
                                    company_id, period, account_id, state, balance, is_must_recalc)
                                select aml.company_id, aml.period, aml.account_id, 
                                    new_state, 
                                    aml.balance, aml.is_must_recalc
                                from z_summary_move aml
                                on conflict (company_id, period, account_id, state)
                                do nothing
                                returning account_move_yearly_balance
                            ), updated_old_state as (
                                update account_move_yearly_balance t
                                set is_must_recalc = true
                                    , balance = t.balance - coalesce(s.balance, 0)
                                from z_summary_move s
                                where s.company_id = t.company_id 
                                    and s.period = t.period
                                    and s.account_id = t.account_id
                                    and s.old_state = t.state
                            )
                            insert into account_move_yearly_balance (
                                company_id, period, account_id, state, balance, is_must_recalc)
                            select aml.company_id, aml.period, aml.account_id, old_state, 
                                0 as balance, true as is_must_recalc
                            from z_summary_move aml
                            on conflict (company_id, period, account_id, state)
                            do nothing;			    
                            -- )
                            -- select * from account_move_yearly_balance s inner join updated_new_state t on t.id = s.id;		    
                    end if;
                end if;
                return NEW;
            end;
            $$;
            
            drop trigger if exists account_move_yearly_balance_triggers on account_move;

            create trigger account_move_yearly_balance_triggers 
                after update 
                on account_move
                for each row execute procedure account_move_yearly_balance_func_triggers();
            
            drop function if exists refresh_account_move_yearly_balance();
            
            create or replace function refresh_account_move_yearly_balance(
             _company_id int, _period int, _account_id int, _state varchar(10)
            )
                returns account_move_yearly_balance
                -- security definer 
                language sql
            as $$
                with z_recalc_result as (
                 select aml.company_id, date_part('year', aml.date) as period, aml.account_id, coalesce(am.state, 'draft') as state, 
                    sum(aml.debit - aml.credit) as balance
            --	 from account_move_yearly_balance m 
            --	  inner join account_move_line aml
            --		on m.company_id = aml.company_id 
            --		and m.period = date_part('year', aml.date) 
            --		and m.account_id = aml.account_id
            -- 	  inner join account_move am on am.id = aml.move_id 
            -- 	  	and am.state = m.state
            -- 	 where m.is_must_recalc = true
                 from account_move_line aml
                    left join account_move am on am.id = aml.move_id 
                 where aml.company_id = _company_id 
                    and date_part('year', aml.date) = _period
                    and aml.account_id = _account_id
                    and am.state = _state
                 group by aml.company_id, date_part('year', aml.date), aml.account_id, am.state
                )	
                update account_move_yearly_balance t
                    set balance = coalesce(s.balance, 0),
                        is_must_recalc = false
            --	from account_move_yearly_balance m left join z_recalc_result s on m.id = s.id
            --	where t.is_must_recalc = true and m.id = t.id
                from account_move_yearly_balance m left join z_recalc_result s 
                    on m.company_id = s.company_id 
                    and m.period = s.period
                    and m.account_id = s.account_id
                    and m.state = s.state
                where t.company_id = _company_id 
                    and t.period = _period
                    and t.account_id = _account_id
                    and t.state = _state
                    and (m.id = t.id)
                returning t.*;
            $$;
            
            drop view if exists account_move_yearly_balance_view;
            
            """)

        # script_view = """
        #     create or replace view account_move_yearly_balance_view as
        #       select r.company_id, r.period, r.account_id, r.state, r.balance, r.is_must_recalc
        #       from account_move_yearly_balance r
        #       where r.is_must_recalc = false
        #       union
        #       select r.company_id, r.period, r.account_id, r.state, n.balance, n.is_must_recalc
        #       from account_move_yearly_balance r
        #         left join refresh_account_move_yearly_balance(
        #             r.company_id, r.period, r.account_id, r.state
        #         ) n on n.id = r.id
        #       where r.is_must_recalc = true;
        #     ;
        #     """

    @api.model_cr
    def create_for_initial_balance_dml(self):
        query = """
            create or replace function account_move_yearly_calculate_balance(
             _company_id int, _period int, _account_id int = 0, _state varchar(10) = ' '
            )
                returns bool
                -- security definer 
                language plpgsql
            as $$
            begin
                with z_recalc_result as (
                 select aml.company_id, date_part('year', aml.date) as period, aml.account_id, coalesce(am.state, 'draft') as state, 
                    sum(aml.debit - aml.credit) as balance
            --	 from account_move_yearly_balance m 
            --	  inner join account_move_line aml
            --		on m.company_id = aml.company_id 
            --		and m.period = date_part('year', aml.date) 
            --		and m.account_id = aml.account_id
            -- 	  inner join account_move am on am.id = aml.move_id 
            -- 	  	and am.state = m.state
            -- 	 where m.is_must_recalc = true
                 from account_move_line aml
                    left join account_move am on am.id = aml.move_id 
                 where aml.company_id = _company_id 
                    and date_part('year', aml.date) = _period
                    and (_account_id = 0 or aml.account_id = _account_id)
                    and (_state = ' ' or am.state = _state)
                 group by aml.company_id, date_part('year', aml.date), aml.account_id, am.state
                )
                , tobe_inserted as (
                    select s.*
                    from z_recalc_result s left join account_move_yearly_balance m 
                        on m.company_id = s.company_id 
                        and m.period = s.period
                        and m.account_id = s.account_id
                        and m.state = s.state
                    where m.id is null		
                )
                , updated as (
                    update account_move_yearly_balance t
                        set balance = coalesce(s.balance, 0),
                            is_must_recalc = false
                --	from account_move_yearly_balance m left join z_recalc_result s on m.id = s.id
                --	where t.is_must_recalc = true and m.id = t.id
                    from account_move_yearly_balance m left join z_recalc_result s 
                        on m.company_id = s.company_id 
                        and m.period = s.period
                        and m.account_id = s.account_id
                        and m.state = s.state
                    where t.company_id = _company_id 
                        and t.period = _period
                        and (_account_id = 0 or t.account_id = _account_id)
                        and (_state = ' ' or t.state = _state)	
                        and (m.id = t.id)
                    returning t.*
                )
                insert into account_move_yearly_balance (
                    company_id, period, account_id, state, balance, is_must_recalc, initial_balance)
                select aml.company_id, aml.period, aml.account_id, 
                    aml.state, 
                    aml.balance, false as is_must_recalc
                    , 0 as initial_balance -- must be recalculate on another function
                from tobe_inserted aml;
                return true;
            end;
            $$;
            
            -- drop function account_move_yearly_check_initial_balance;
            create or replace function account_move_yearly_check_initial_balance(
                _company_id int default 0, _period int default 0, _show_not_balance_only bool = false
                ) returns table (
                    initial_balance numeric,
                    last_end_balance numeric,
                    previous_profits numeric,
                    user_type_id int,
                    last_init_balance numeric,
                    last_balance numeric,
                    current_balance numeric,
                    include_initial_balance bool,
                    id int,
                    company_id int,
                    account_id int,
                    period int, 
                    state varchar
                )
                 language plpgsql
            as $$
            begin
                return query
                    select t.initial_balance, 
                    case when at.include_initial_balance then 
                            coalesce(s.initial_balance, 0) + coalesce(s.balance, 0) else 0 end
                            + case when a.user_type_id = 12 then coalesce(prof.previous_year_profits, 0) else 0 end			
                        as last_end_balance 
                    , prof.previous_year_profits as previous_profits, a.user_type_id
                    , s.initial_balance as last_init_balance
                    , s.balance as last_balance, t.balance as current_balance
                    , at.include_initial_balance, 
                    t.id, t.company_id, t.account_id, t.period, t.state
                    from account_move_yearly_balance t
                        left join account_account a on a.id = t.account_id
                        left join account_account_type at on at.id = a.user_type_id
                        left join account_move_yearly_balance s on s.company_id = t.company_id 
                            and s.period = t.period - 1
                            and s.account_id = t.account_id
                            and s.state = t.state
                        left join account_move_yearly_previous_year_profits_12(t.company_id, t.period) prof on prof.user_type_id = 12
                    where t.company_id = 1 and t.period = 2020
                    and (not _show_not_balance_only or 
                        t.initial_balance != (
                            case when at.include_initial_balance then 
                                coalesce(s.initial_balance, 0) + coalesce(s.balance, 0) else 0 end
                                + case when a.user_type_id = 12 then coalesce(prof.previous_year_profits, 0) else 0 end	
                        )
                    )
                    order by t.id;
            end;
            $$;

            -- drop function public.account_move_yearly_balance_check;
            -- drop function account_move_yearly_previous_year_profits_12;
            
            create or replace function account_move_yearly_previous_year_profits_12(
                _company_id int default 0, _period int default 0 
                ) returns table (
                    previous_year_profits numeric,
                    user_type_id int
                )
                 language plpgsql
            as $$
            begin
                return query 
                    select sum(t.balance) as previous_year_profits, 12::int as user_type_id
                    from account_move_yearly_balance t
                    left join account_account a on a.id = t.account_id
                    left join account_account_type at on at.id = a.user_type_id
                    where t.company_id = _company_id and t.period = _period - 1
                    and at.include_initial_balance = false;
            end;
            $$;
            
            -- drop function account_move_yearly_calculate_init_balance;
            create or replace function account_move_yearly_calculate_init_balance(
                _company_id int default 0, _period int default 0, _calculate_all_year bool = true
                ) returns bool
              -- security definer
              language plpgsql
            as $$
            /* calculate initial/beginning balance per account for company A and year X
            
                -- calculate balance on company A and year X
                select account_move_yearly_calculate_balance(1, 2019);
                -- calculate initial/beginning balance on company A and year X
                select account_move_yearly_calculate_init_balance(1,2020);
                
                -- check data
                select * from account_move_yearly_check_initial_balance(1, 2020, false);
                --- show invalid initial balance
                select * from account_move_yearly_check_initial_balance(1, 2020, true);
            
             */
            declare 
                _total_current_year_earnings numeric;	
                _calculate_balance bool;
            begin
                if _company_id = 0 or _period = 0 then
                    return false;
                end if;
                -- refresh previous year balance first
                if _calculate_all_year then
                    select account_move_yearly_calculate_balance(_company_id, _period) into _calculate_balance;
            --	else
                    -- -- calculate only data that have changes (is_must_recalculate = true)
            --		select * from account_move_yearly_view;
                end if;
            
                drop table if exists z_balance_last_year;
            
                create temp table z_balance_last_year as 
                    select s.id, s.company_id, s."period", s.account_id, s.state, 
                        s.is_must_recalc, s.balance, s.initial_balance
                        , a.user_type_id, at.include_initial_balance
                    from account_move_yearly_balance s 
                        left join account_account a on a.id = s.account_id
                        left join account_account_type at on at.id = a.user_type_id
                    where s.company_id = _company_id and s.period = _period - 1
                    ;
                
                IF NOT EXISTS (SELECT 1 FROM z_balance_last_year p WHERE p.user_type_id = 12) THEN
                    -- make sure data with user_type_id = 12 exists
                    insert into z_balance_last_year 
                        (company_id, "period", account_id, state, is_must_recalc, balance, initial_balance,
                        user_type_id, include_initial_balance)
                    SELECT a.company_id, _period as period, a.id as account_id, 'posted' as state, false as is_must_recalc ,
                        0 as balance, 0 as initial_balance,
                        a.user_type_id, at.include_initial_balance
                    from account_account a
                        left join account_account_type at on at.id = a.user_type_id
                    where a.user_type_id = 12;
                END IF;
            
                -- insert data that not yet exists in period X		
                insert into account_move_yearly_balance (
                    company_id, period, account_id, state, is_must_recalc, balance, initial_balance)
                select s.company_id, 
                    _period as period, s.account_id, 
                    s.state, false as is_must_recalc,
                    0 as balance
                    , 0 as initial_balance -- will be recalculate later
                from z_balance_last_year s 
                left join account_move_yearly_balance t on s.company_id = t.company_id 
                        and t.period = _period
                        and s.account_id = t.account_id
                        and s.state = t.state
                where t.id is null;
                
            --	select * From account_account_type;
                
                -- untuk account yang pada account type-nya include_initial_balance-nya "false" 
                -- akan masuk ke initial balance account yg account type-nya Current Year Earning (user_type_id : 12)
                --select sum(balance) into _total_current_year_earnings from z_balance_last_year 
                --	where include_initial_balance = false;
                
                -- calculate initial/beginning balance
                --  beginning balance year X = [beginning balance year X-1] + [balance year X-1]
                --   khusus utk user_type_id = 12, update with total current year earning 
                update account_move_yearly_balance t
                    set initial_balance =  
                        case when s.include_initial_balance then s.initial_balance + s.balance else 0 end
                        + case when s.user_type_id = 12 then coalesce(prof.previous_year_profits, 0)  else 0 end
                from z_balance_last_year s 
                left join account_move_yearly_previous_year_profits_12(s.company_id, s.period) prof 
                    on prof.user_type_id = s.user_type_id
                where t.company_id = s.company_id 
                    and t.period = _period
                    and t.account_id = s.account_id
                    and t.state = s.state;
                return true;
            end;
            $$;
"""
        self._cr.execute(query)

