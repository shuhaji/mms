
wkhtmltopdf version for specific odoo: https://github.com/odoo/odoo/wiki/Wkhtmltopdf

https://medium.com/@hendrasj/install-odoo-12-and-wkhtmltopdf-on-ubuntu-18-04-or-debian-9-160c2e10f123

- Install Wkhtmltopdf 0.12.5–1 on Ubuntu 18.04:
    1. Download Wkhtmltopdf package for Ubuntu 18.04 from repository:
        wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb
    2. Install Wkhtmltopdf package:
        sudo dpkg -i wkhtmltox_0.12.5-1.bionic_amd64.deb
    3. Install dependency package
        sudo apt install -f

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