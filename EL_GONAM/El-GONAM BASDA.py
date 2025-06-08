import csv
import hashlib
import psycopg2
import pandas as pd
import os

def postgresql_connect():
    conn = psycopg2.connect(
        dbname="qurban_el_gonam",
        user="postgres",
        password="elgonamku",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    return conn, cur

def postgresql_commit_nclose(conn, cur):
    conn.commit()
    boolean = cur.rowcount
    cur.close()
    conn.close()
    return boolean

def postgresql_cls(conn, cur):
    cur.close()
    conn.close()

def id_berikutnya(filename):
    try:
        with open(filename, mode="r") as file:
            reader = csv.reader(file)
            rows = list(reader)
            if rows:
                return int(rows[-1][0]) + 1
    except FileNotFoundError:
        pass
    return 1

def main_menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n=== Selamat Berqurban di EL-GONAM ===")
    print("[1] Registrasi")
    print("[2] Login")
    print("[3] Keluar")
    pilihan = input("Pilih: ")

    if pilihan == '1':
        register()
    elif pilihan == '2':
        login()
    elif pilihan == '3':
        print("Sampai jumpa!")
        exit()
    else:
        print("Pilihan tidak valid.")
        main_menu()

def register():
    os.system('cls' if os.name == 'nt' else 'clear')
    filename = "users.csv"

    if not os.path.isfile(filename) or os.path.getsize(filename) == 0:
        users_df = pd.DataFrame(columns=["user_id", "nama", "username", "password", "nomor_hp", "role"])
    else:
        users_df = pd.read_csv(filename)

    user_id = 1 if users_df.empty else users_df["user_id"].max() + 1

    nama = input("Masukkan Nama: ")
    username = input("Masukkan username: ")
    password = input("Masukkan password: ")
    nomor_hp = input("Masukkan Nomor HP: ")
    alamat = input("Masukkan Alamat: ")
    role = "user"
    
    password = hashlib.sha256(password.encode()).hexdigest()

    # Buat DataFrame dari data baru
    new_user_df = pd.DataFrame([{"user_id": user_id, "username": username, "password": password, "role": role, "nama": nama, "nomor_hp": nomor_hp, "alamat": alamat}])

    # Tambahkan baris baru ke DataFrame lama dengan concat
    users_df = pd.concat([users_df, new_user_df], ignore_index=True)

    # Simpan ke file CSV
    users_df.to_csv(filename, index=False)
    print("Registrasi berhasil!")
    main_menu()

def login():
    os.system ('cls')
    print("=== Login ===")
    username = input("Masukkan Username: ").strip()
    password = input("Masukkan Password: ").strip()

    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        with open("users.csv", mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[2] == username and row[3] == password_hash:
                    print(f"Login berhasil! Selamat datang, {row[1]}")
                    show_menu(role=row[5], user_id=row[0], nama=row[1])
                    os.system ('cls')
                    return
    except FileNotFoundError:
        print("Belum ada data pengguna. Silakan registrasi.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

    print("Email atau password salah. Coba lagi.")
    os.system ('cls')
    main_menu()

def show_menu(role, user_id, nama):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n=== Menu Utama ===")
    if role == "user":
        print("[1] Daftar Hewan")
        print("[2] Lihat Tabungan")
        print("[3] Setor Tabungan")
        print("[4] Pengajuan Qurban")
        print("[5] Jadwal Pemotongan")
        print("[6] Logout")
        pilihan = input("Pilih menu: ")

        if pilihan == '1':
            daftar_hewan()
        elif pilihan == '2':
            lihat_tabungan(role, nama, user_id)
        elif pilihan == '3':
            setor_tabungan(role, nama)
        elif pilihan == '4':
            pengajuan_qurban(user_id)
        elif pilihan == '5':
            lihat_jadwal(user_id)
        elif pilihan == '6':
            print("Klik enter untuk keluar")
        else:
            print("Pilihan tidak valid.")
            show_menu(role, user_id, nama)

# === FITUR ===
def daftar_hewan():
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        conn, cur = postgresql_connect()
        cur.execute('SELECT hewan_id, jenis_hewan, berat, harga FROM hewan_qurban')
        data = cur.fetchall()
        print("\n=== Daftar Hewan Qurban ===")
        for row in data:
            print(f"ID: {row[0]}, Jenis: {row[1]}, Berat: {row[2]}, Harga: {row[3]}")
        postgresql_cls(conn, cur)
        input("Tekan Enter untuk kembali...")
    except Exception as e:
        print(f"[ERROR] Gagal ambil data: {e}")
        input("Tekan Enter untuk kembali...")
        show_menu()

def lihat_tabungan(role, nama_pembeli, user_id):
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        conn, cur = postgresql_connect()
        cur.execute('''
            SELECT SUM(nominal_setoran) 
            FROM setoran_tabungan 
            WHERE nama_pembeli = %s
        ''', (nama_pembeli,))
        total = cur.fetchone()[0] or 0
        print(f"\nTotal Tabungan Anda, {nama_pembeli}: Rp {total}")
    except Exception as e:
        print(f"[ERROR] Gagal mengambil data tabungan: {e}")
    finally:
        postgresql_cls(conn, cur)
        input("Tekan Enter untuk kembali...")
        show_menu(role=role, user_id=user_id, nama=nama_pembeli)


def setor_tabungan(role, nama_pembeli):
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Pilih rekening bank tujuan
    no_rekening_bank = pilih_metode_pembayaran()
    if not no_rekening_bank:
        print("Gagal memilih metode pembayaran.")
        return

    try:
        no_rek_pembeli = input("Masukkan Nomor Rekening Anda: ").strip()
        jumlah = int(input("Masukkan jumlah setoran: "))
        status = input("Masukkan status setoran (Terkonfirmasi/Tertunda): ").strip()

        if status not in ['Terkonfirmasi', 'Tertunda']:
            print("Status tidak valid. Setoran dibatalkan.")
            return

        conn, cur = postgresql_connect()
        cur.execute('''INSERT INTO setoran_tabungan 
                       (tanggal_setor, nominal_setoran, status, no_rek_pembeli, nama_pembeli, no_rekening)
                       VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)''',
                    (jumlah, status, no_rek_pembeli, nama_pembeli, no_rekening_bank))
        conn.commit()
        print("Setoran berhasil ditambahkan!")
    except Exception as e:
        print(f"[ERROR] Gagal menyetor tabungan: {e}")
    finally:
        postgresql_cls(conn, cur)
        input("Tekan Enter untuk kembali...")
        show_menu(role=role, user_id=no_rek_pembeli, nama=nama_pembeli)



def pilih_metode_pembayaran():
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        conn, cur = postgresql_connect()
        cur.execute('SELECT no_rekening, nama_bank FROM metode_pembayaran')
        metode_list = cur.fetchall()

        print("\n=== Pilih Metode Pembayaran ===")
        for i, (no_rek, bank) in enumerate(metode_list, start=1):
            print(f"[{i}] {bank} - No. Rek: {no_rek}")

        pilihan = int(input("Pilih nomor metode pembayaran: "))
        if 1 <= pilihan <= len(metode_list):
            no_rekening_terpilih = metode_list[pilihan - 1][0]
            return no_rekening_terpilih
        else:
            print("Pilihan tidak valid.")
            return None
    except Exception as e:
        print(f"[ERROR] Gagal ambil data metode pembayaran: {e}")
        return None
    finally:
        postgresql_cls(conn, cur)


def pengajuan_qurban(user_id):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"[DEBUG] user_id yang aktif: {user_id}")
    try:
        conn, cur = postgresql_connect()

        # Ambil nama pembeli berdasarkan user_id
        cur.execute('SELECT nama FROM "user" WHERE user_id = %s', (user_id,))
        result = cur.fetchone()
        if not result:
            print("User tidak ditemukan.")
            return
        nama_pembeli = result[0]

        # Total tabungan user
        cur.execute("""
            SELECT SUM(nominal_setoran) 
            FROM setoran_tabungan 
            WHERE nama_pembeli = %s AND status = 'Terkonfirmasi'
        """, (nama_pembeli,))
        total = cur.fetchone()[0] or 0

        # Tampilkan daftar hewan qurban
        cur.execute("SELECT hewan_id, jenis_hewan, berat, harga FROM hewan_qurban")
        hewan_list = cur.fetchall()
        print("\n=== Pilih Hewan Qurban ===")
        for h in hewan_list:
            print(f"[{h[0]}] {h[1]} - Berat: {h[2]}kg - Harga: Rp {h[3]}")
        
        hewan_id = input("Masukkan ID Hewan yang ingin diajukan: ").strip()

        # Validasi hewan yang dipilih
        cur.execute("SELECT harga FROM hewan_qurban WHERE hewan_id = %s", (hewan_id,))
        row = cur.fetchone()
        if not row:
            print("ID Hewan tidak valid.")
            return
        harga_hewan = row[0]

        if total >= harga_hewan:
            # Cek apakah user sudah mengajukan
            cur.execute("SELECT COUNT(*) FROM pengajuan WHERE user_id = %s", (user_id,))
            sudah_ada = cur.fetchone()[0]
            if sudah_ada > 0:
                print("Anda sudah mengajukan qurban sebelumnya.")
            else:
                cur.execute('''
                    INSERT INTO pengajuan (user_id, hewan_id, status_pengajuan, tanggal_pengajuan)
                    VALUES (%s, %s, 'Menunggu Persetujuan Admin', CURRENT_DATE)
                ''', (user_id, hewan_id))
                conn.commit()
                print("Pengajuan berhasil dikirim.")
        else:
            print(f"Tabungan Anda belum mencukupi. Harga hewan: Rp {harga_hewan}, Tabungan: Rp {total}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        postgresql_cls(conn, cur)
        input("Tekan Enter untuk kembali...")



def lihat_jadwal(user_id):
    os.system('cls' if os.name == 'nt' else 'clear')
    try:
        conn, cur = postgresql_connect()
        cur.execute('''
    SELECT jp.tanggal_penyaluran, jp.lokasi
    FROM pengajuan p
    JOIN jadwal_pemotongan jp ON p.jadwal_id = jp.jadwal_id
    WHERE p.user_id = %s
''', (user_id,))
        data = cur.fetchone()
        if data:
            print("\n=== Jadwal Pemotongan Anda ===")
            print(f"Tanggal: {data[0]}")
            print(f"Lokasi : {data[1]}")
        else:
            print("Belum ada jadwal pemotongan untuk Anda.")
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        postgresql_cls(conn, cur)
        input("Tekan Enter untuk kembali...")

if __name__ == "__main__":
    main_menu()
