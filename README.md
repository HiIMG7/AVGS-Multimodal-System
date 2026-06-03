# AVGS-Multimodal-System
AVGS
# AVGS: 智能影音生成系統 (Virtual General-purpose Speaker)

本專案為碩士論文之核心實作成果，成功開發一套端到端（End-to-End）的多模態影音流水線系統。

---

## 硬體設備需求與環境但書

本系統在底層設計上兼顧了「極致效能」與「跨平台相容性」，影音縫合引擎依據運行環境之硬體規格，拆分為以下兩種配置模式：

### 1. 推薦硬體配置（調度渦輪極速引擎）
若欲達到論文所述之最佳渲染效能，系統執行環境建議具備以下規格，以利啟動 `AVGS_Movie_Turbo.py` 進行硬體級加速：
* 顯示卡 (GPU)：必須配備 NVIDIA 獨立顯示卡（建議 RTX 4060 或同等類型以上），且系統需安裝支援 CUDA 之外顯驅動程式，以召喚 FFmpeg 底層之 `h264_nvenc` 硬體編碼加速引擎。
* 處理器 (CPU)：Intel Core i7 / AMD Ryzen 7 以上。
* 記憶體 (RAM)：16 GB 以上。

### 2. 最低硬體配置（調度穩定相容引擎）
若運行環境未配備 NVIDIA 獨立顯示卡（例如僅有 Intel/AMD 內建顯示晶片、使用 Mac 系統、或於無 GPU 之 Linux 雲端環境部署），系統依然可以正常完整運行：
* 顯示卡 (GPU)：無外顯需求，支援內建顯示晶片或純 CPU 運算。
* 處理器 (CPU)：具備多核心之處理器（系統預設調度 8 核心進行非同步加速）。
* 效能但書：使用者僅需於前端控制台（`AVGS_Web.py`）將渲染引擎切換為「穩定相容模式」。該模式會轉由 `AVGS_Movie.py` 調度 CPU 多執行緒與 MoviePy 原生編碼器進行影音縫合；唯缺乏獨顯之硬體級加速，整體影片的後製渲染耗時將會顯著增加，屬於架構設計上的資源權衡。

---

## 金鑰設定與 JSON Config 用法

本系統所有的第三方雲端 API 金鑰與語音參數，統一由專案根目錄下的 `config.json` 進行集中管理。為了維護資訊安全，請勿將包含真實金鑰的 config 檔案推上公開倉庫。

### 1. 建立設定檔
請在與程式碼同級的資料夾下，手動建立一個名為 `config.json` 的純文字檔案。

### 2. 配置內容範例
請將以下 JSON 結構複製到 `config.json` 中，並將對應欄位替換為你個人的真實 API Key：

{
  "gemini_key": "YOUR_GEMINI_API_KEY",
  "elevenlabs_key": "YOUR_ELEVENLABS_API_KEY",
  "did_key": "YOUR_DID_API_KEY",
}

### 3. 欄位填寫說明
* gemini_key：填入 Google AI Studio 申請的 Gemini 2.5 憑證。
* elevenlabs_key：填入 ElevenLabs 帳戶中的個人 API 金鑰（用於高品質語音合成）。
* did_key：填入 D-ID 平台申請的 Basic 認證密鑰（格式通常為 Basic 後方加上一串 Base64 編碼，用於虛擬主播生成）。
* voice_id：指定 ElevenLabs 的發音人 ID（預設 `nPczCjzI2devNBz1zQrb` 為系統實測之男性聲音參數）。

---

## 快速開始與執行步驟

完成金鑰設定後，請開啟終端機（Terminal / Command Prompt），依序執行以下指令以啟動系統控制台介面：

1. 切換至專案根目錄
使用 `cd` 指令進入本專案原始碼存放的資料夾路徑（請根據您本機的實際路徑調整）：
cd path/to/AVGS-Multimodal-System

2. 安裝必要依賴套件
首次執行前，請確保已安裝系統所需之核心 Python 庫：
pip install streamlit google-genai pillow imageio-ffmpeg moviepy requests

3. 啟動 Streamlit 前端網頁
執行以下指令，系統會自動在瀏覽器中開啟 AVGS 智能影音生成系統的互動控制台：
streamlit run AVGS_Web.py
專案結構說明
AVGS_Gemini.py - 視覺文本多模態解析大腦（JSON 結構化輸出）

AVGS_Audio.py - 高擬真多語言語音合成模組

AVGS_Vision.py - 自動折行與縮放的投影片圖卡渲染引擎

AVGS_Avatar.py - 虛擬主播生成與「先合併後切割」優化器

AVGS_Movie_Turbo.py - FFmpeg + NVIDIA 獨顯硬體加速縫合核心

AVGS_Movie.py - MoviePy + CPU 多執行緒穩定備援縫合核心

AVGS_Web.py - Streamlit 雙模式互動控制台 UI
