Setup Awal untuk Development
----------------------------

    Prequisite:
    - Instal Git (termasuk Git Bash-nya)
    - Python 3.5
      http://timmyreilly.azurewebsites.net/python-pip-virtualenv-installation-on-windows/
    - VS Code atau PyCharm (rekomendasi pyCharm, install yg community edition)
    - Database PostgreSQL (minimal versi 10), bisa di localhost atau di server lain.

### Setup Awal:

- Buat Folder kosong di komputer local
  misal: c:\odoo
- di dalam folder tsb, buat dua folder
  - custom (untuk menyimpan custom code dari KG)
  - server (untuk menyimpan source code asli dari Odoo)
  
- Copy source code Custom Code dari KG ke dalam folder custom
  (jika belum punya akses ke git repository KG CITIS, langkah ini bisa dilewati dulu)
  
  - pastikan ssh public key kita sudah terdaftar di user Azure Devops kita:
    https://docs.microsoft.com/en-us/azure/devops/repos/git/use-ssh-keys-to-authenticate?view=azure-devops)
  - Klik kanan folder custom, pilih “Git Bash Here” 
  - Download source code dg mengetik di dalam command prompt Git Bash: 

    ```
    cd c:\odoo\custom

    ### Download code via https (jika belum setup ssh 
    git clone kgcitis@vs-ssh.visualstudio.com:v3/kgcitis/Odoo/Odoo . 
    ### Atau jika sudah setup SSH: 
    git clone git@ssh.dev.azure.com:v3/kgcitis/Odoo/Odoo . 
    ### (PENTING: pastikan ada tanda titik di UJUNG perintah, kemudian tekan enter, tunggu sampai selesai) 
   
    git checkout -b develop origin/develop
    ```
    
- petunjuk selengkapnya bisa di baca di: 
   Odoo\custom\docs\dev_setup_awal.md
   
Selanjutnya:
 
- Copy source code asli Odoo ke folder Odoo\Server
    
    ```
    cd c:\odoo\server     
    git clone https://github.com/OCA/OCB.git .
    ```
    
    - PENTING: perhatikan tanda TITIK di akhir baris ini, tidak boleh ketinggalan
      ini untuk meng-clone code ke dalam CURRENT FOLDER
    
    - Pindah ke branch Odoo versi 11.0 (ini yg kita pakai saat ini) 
    
    ```
    git checkout 11.0
    ```
    
- Set file odoo.conf
    - copy dari c:\odoo\custom\docs\odoo.conf ke folder c:\odoo (c:\odoo\odoo.conf)
    - edit configurasi sesuai kebutuhan (host server database, dll)

- Setup Python Virtual Environment (jika OS Windows - masuk ke git bash)
    - misal bikin virtual environment "odoo11"
      petunjuk lengkap tentang virtual env di windows bisa dibaca jg di: 
      https://timmyreilly.azurewebsites.net/python-pip-virtualenv-installation-on-windows/

  (utk OS selain windows, hilangkan syntax .bat, .bat hanya utk windows command prompt)
    ```bash
    pip install virtualenv
    pip install virtualenvwrapper-win
  
    # Create Virtual Environment:
    mkvirtualenv.bat odoo11
    #  (file2 library python akan ditaruh di home directory folder Envs, 
    #    misal: cd %HOMEPATH%\Envs (atau cd ~/Envs)
  
    # Keluar dari virtual environment yg aktif
    deactivate.bat
  
    # masuk ke virtual environment yg sudah pernah dibuat:
    workon odoo11
    # (atau)
    workon.bat odoo11

    # masuk ke folder project kita:
    cd c:\odoo
  
    # bind virtual environment ke project folder kita:
    setprojectdir .
    # contoh:
    # (odoo11) c:\odoo\setprojectdir .
  
    # utk tahu path ke virtual env tsb:
    which python3
    # contoh hasil: c/Program Files (x86)/Microsoft Visual Studio/Shared/Python36_64/python
    #  Path ini nanti digunakan utk mengeset 
  
    ```
- Install Requirements:
    ```bash
    workon.bat odoo11
    pip install -r c:\odoo\server\requirements
    # (jika komponen yg gagal diinstall di windows/ada error, baca pentunjuk di bawah)
    ```

- jalankan odoo lewat command prompt:
    ```
    workon.bat odoo11
    cd c:\odoo
    python server/odoo-bin --config=odoo.conf 
    
    #  run + hot reload:
    python server/odoo-bin --config=odoo.conf --dev=all 
    
    #  run dg log level tertentu:
    python server/odoo-bin --config=odoo.conf --dev=all --log-handler=:DEBUG
    
    #  run and upgrade module kg_pos:
    python server/odoo-bin --config=odoo.conf -u kg_pos
    #  run and upgrade all modules:
    python server/odoo-bin --config=odoo.conf -u all
    
    #  add new module:
    odoo-bin scaffold <module name> <where to put it>
    python server/odoo-bin scaffold kg_quiz_exam  ./custom/local
    ```      
    
- Jika anda menggunakan PyCharm:
  - Buka PyCharm
  - Buka folder: File - Open
    pilih folder utama kita di atas (c:\odoo)
  - klik kanan di folder custom
    pilih: "Mark Directory as" --> "Source Root"
  - klik kanan di folder server
    pilih: "Mark Directory as" --> "Source Root"
  - Penting: Set Project Intepreter:
     - File
        - Settings
            - Project Intepreter
                - klik tanda roda di kanan atas, pilih Add (jika belum ada)
                    - pilih Existing
                        - pilih python.exe di dalam virtual environment "odoo11" yg kita buat di atas
                            (biasanya di folder: c:\Users\NamaUser\Envs\NamaVirtualEnvironment\Scripts 
                             misal: C:\Users\Aan\Envs\odoo11\Scripts\Python.exe)
    
- Khusus windows: jika saat install requirements.txt ada error dan ada warning: 
  "blabla C++ build tools dibutuhkan utk installasi,"
     
  ```
    download dan install langsung aja dari:
    https://www.lfd.uci.edu/~gohlke/pythonlibs/
    --- misal utk versi 11.0, akan ada 2 library yg error: psycopg2 dan reportlab
    https://www.lfd.uci.edu/~gohlke/pythonlibs/#reportlab
    https://www.lfd.uci.edu/~gohlke/pythonlibs/#psycopg2
    --- download file yg sesuai: 
    ----- cpXX == versi python yg ada di computer kita 
    ----- win32 vs win_amd64 === versi python kita apakah win32 atau win 64, utk ngecek: type:
    --- c:\python 
    contoh output: "Python 3.6.6 (v3.6.6:4cf1f54eb7, Jun 27 2018, 03:37:03) [MSC v.1900 64 bit (AMD64)] on win32"
     ----> berarti python versi 3.6 dan 64 bit
    
    misal download file: psycopg2-2.7.5-cp36-cp36m-win32.whl, taruh di c:\000_pindahaan\
      note: cp36 artinya: utk Python versi 3.6.x
       dowload file yg sesuai
    trus install dg:
    pip3 install d:\psycopg2-2.7.5-cp36-cp36m-win32.whl
    --- misal utk yg 64 bit python 3.6
    pip3 install c:\000_pindahaan\psycopg2-2.7.5-cp36-cp36m-win_amd64.whl
    pip3 install c:\000_pindahaan\reportlab-3.5.11-cp36-cp36m-win_amd64.whl
    
    
    jika saat run ada error: "ModuleNotFoundError: No module named 'PyPDF2'"
    -- install dulu:
    pip install PyPDF2
    ```
    
- jika ada error "Could not execute command 'lessc'":
    1. install node.js (download dari: https://nodejs.org/en/)
    2. setelah selesai, buka windows command prompt, jalankan di command prompt:
    
       `npm install -g less`
    3. done
    
- WkthtmlToPdf on windows:
    - download wkthtmltopdf installer (utk odoo 11 versi 0.12.5):
        https://wkhtmltopdf.org/downloads.html
        (sesuai versi windows masing2)
    - install (jalankan exe installer)
    - PENTING: tambahkan path %install%wkhtmltopdf%\bin ke windows path
        (misal: C:\Program Files\wkhtmltopdf\bin)
        Windows Explorer - This PC - klik kanan - Properties - "Advance System Settings"
            di Environmet Variables - System Variables - PATH
                klik New - tambahkan C:\Program Files\wkhtmltopdf\bin


        