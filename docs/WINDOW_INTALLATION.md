# 🪟 Windows Installation Guide

## bl1nk-agent-builder สำหรับ Windows

คู่มือการติดตั้งและใช้งาน bl1nk-agent-builder บนระบบปฏิบัติการ Windows

## 📋 ข้อกำหนดระบบ

### ซอฟต์แวร์ที่จำเป็น

1. **Python 3.9+** 📦
   - ดาวน์โหลดจาก: https://python.org/downloads/
   - ⚠️ **สำคัญ**: เลือก "Add Python to PATH" ระหว่างการติดตั้ง

2. **Node.js 18+** 📦
   - ดาวน์โหลดจาก: https://nodejs.org/
   - เลือก LTS version

3. **Git for Windows** 📦
   - ดาวน์โหลดจาก: https://git-scm.com/download/win
   - แนะนำให้ติดตั้ง Git Bash สำหรับความเข้ากันได้ที่ดีกว่า

4. **Docker Desktop (แนะนำ)** 📦
   - ดาวน์โหลดจาก: https://www.docker.com/products/docker-desktop
   - สำหรับการพัฒนาแบบ containerized

### ซอฟต์แวร์เสริม (ไม่บังคับ)

- **Visual Studio Code** - Editor แนะนำ
- **Windows Terminal** - Terminal ที่ดีกว่า
- **WSL2** - Linux environment บน Windows (แนะนำสำหรับผู้ใช้ขั้นสูง)

---

## 🚀 การติดตั้ง

### วิธีที่ 1: ใช้ Bootstrap Script (แนะนำ)

1. **เปิด Command Prompt หรือ PowerShell**
   ```cmd
   # ไปที่โฟลเดอร์โปรเจ็ค
   cd path\to\bl1nk-agent-builder
   ```

2. **รัน Bootstrap Script**
   ```cmd
   # ใช้ batch file
   bootstrap.bat

   # หรือใช้ Git Bash
   bash scripts/bootstrap.sh development
   ```

3. **ติดตามขั้นตอนบนหน้าจอ**
   - Script จะตรวจสอบ prerequisites
   - ติดตั้ง dependencies
   - สร้าง project structure
   - สร้าง environment files

### วิธีที่ 2: ติดตั้งแบบ Manual

1. **ติดตั้ง Python Dependencies**
   ```cmd
   cd apps\worker
   python -m venv ..\..\.venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   cd ..\..
   ```

2. **ติดตั้ง Node.js Dependencies**
   ```cmd
   cd apps\bridge
   npm install
   cd ..\..
   
   cd ui\nextjs
   npm install
   cd ..\..
   ```

3. **สร้าง Environment File**
   ```cmd
   copy config\env.example .env
   # แก้ไข .env ด้วยค่าของคุณ
   ```

---

## 🏃‍♂️ เริ่มต้นใช้งาน

### เริ่มต้น Development Environment

```cmd
# ใช้ batch script
start.bat

# หรือเริ่มทีละส่วน
# 1. เริ่ม database และ cache (ถ้าใช้ Docker)
docker-compose up -d postgres redis

# 2. เริ่ม FastAPI
cd apps\worker
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. เริ่ม Cloudflare Worker (ใน terminal ใหม่)
cd apps\bridge
wrangler dev

# 4. เริ่ม Next.js UI (ใน terminal ใหม่)
cd ui\nextjs
npm run dev
```

### หยุด Services

```cmd
# ใช้ batch script
stop.bat

# หรือหยุดทีละส่วน
docker-compose down
# ปิด terminal windows ที่เปิดไว้
```

---

## 🔧 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

#### 1. Python ไม่พบ
```cmd
# ตรวจสอบ Python installation
python --version

# ถ้าไม่พบ ให้เพิ่ม Python ใน PATH
# หรือใช้ py command แทน
py --version
py -m pip install -r requirements.txt
```

#### 2. Node.js ไม่พบ
```cmd
# ตรวจสอบ Node.js installation
node --version
npm --version

# ถ้าไม่พบ ให้รีสตาร์ท Command Prompt
# หรือใช้ Git Bash แทน
```

#### 3. Git ไม่พบ
```cmd
# ตรวจสอบ Git installation
git --version

# ถ้าไม่พบ ให้ติดตังจาก https://git-scm.com/
# และเลือก "Git Bash" ในการติดตั้ง
```

#### 4. Permission Denied
```cmd
# เปิด Command Prompt ในฐานะ Administrator
# หรือใช้ Git Bash ที่มี permission ที่ดีกว่า
```

#### 5. Docker ไม่ทำงาน
```cmd
# ตรวจสอบ Docker Desktop
docker --version

# ถ้าไม่ทำงาน ให้เริ่ม Docker Desktop ก่อน
# หรือข้ามการใช้ Docker และใช้ manual setup แทน
```

### Windows-Specific Solutions

#### ใช้ Git Bash แทน Command Prompt
```bash
# เปิด Git Bash แทน
./bootstrap.sh development
./start.sh
```

#### ใช้ PowerShell แทน Command Prompt
```powershell
# เปิด PowerShell
.\bootstrap.bat
.\start.bat
```

#### WSL2 Integration
```bash
# ถ้าติดตั้ง WSL2 แล้ว ใช้ Linux commands ได้
wsl
cd /mnt/c/path/to/bl1nk-agent-builder
./bootstrap.sh development
```

---

## 🛠️ Development Workflow

### การพัฒนาแอปพลิเคชัน

1. **เริ่ม Development Environment**
   ```cmd
   start.bat
   ```

2. **เปิด Editor (VS Code แนะนำ)**
   ```cmd
   code .
   ```

3. **แก้ไขโค้ดใน apps/worker/ สำหรับ FastAPI**

4. **แก้ไขโค้ดใน apps/bridge/ สำหรับ Cloudflare Worker**

5. **แก้ไขโค้ดใน ui/nextjs/ สำหรับ UI**

6. **ทดสอบการทำงานที่:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Worker: http://localhost:8787
   - UI: http://localhost:3000

### การจัดการ Database

```cmd
# เชื่อมต่อ PostgreSQL (ถ้าใช้ Docker)
docker exec -it bl1nk_postgres psql -U bl1nk -d bl1nk

# หรือใช้ GUI tool เช่น pgAdmin
```

### การจัดการ Dependencies

```cmd
# อัพเดท Python dependencies
cd apps\worker
.venv\Scripts\activate
pip-compile requirements.in
pip install -r requirements.txt

# อัพเดท Node.js dependencies
cd ..\bridge
npm update
cd ..\..
```

---

## 📚 แหล่งข้อมูลเพิ่มเติม

### Documentation
- [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - คู่มือเริ่มต้น
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - สรุปโปรเจ็ค
- [README.md](README.md) - เอกสารหลัก

### Windows-Specific Resources
- [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/)
- [Git for Windows Guide](https://git-scm.com/download/win)
- [Node.js Windows Installation](https://nodejs.org/en/download/)
- [Python Windows Installation](https://docs.python.org/3/using/windows.html)

### เครื่องมือแนะนำ
- **Terminal**: Windows Terminal, Git Bash, PowerShell
- **Editor**: Visual Studio Code, Sublime Text
- **Database GUI**: pgAdmin, DBeaver
- **API Testing**: Postman, Insomnia

---

## ❓ การขอความช่วยเหลือ

### การรายงานปัญหา

หากพบปัญหา:

1. **ตรวจสอบ Prerequisites**
   - Python 3.9+
   - Node.js 18+
   - Git for Windows
   - Docker Desktop (แนะนำ)

2. **ดู Logs**
   ```cmd
   # ตรวจสอบ console output
   # เปิด Developer Tools ใน browser สำหรับ UI
   ```

3. **ทดสอบแบบ Minimal**
   ```cmd
   # ทดสอบ Python
   python --version
   python -c "print('Hello World')"
   
   # ทดสอบ Node.js
   node --version
   node -e "console.log('Hello World')"
   
   # ทดสอบ Git
   git --version
   ```

### การติดต่อ

- 📧 **Email**: support@bl1nk.site
- 💬 **GitHub Issues**: [สร้าง Issue ใหม่](https://github.com/UnicornXOS/bl1nk-stack-builder/issues)
- 📖 **Documentation**: [docs.bl1nk.dev](https://docs.bl1nk.site)

---