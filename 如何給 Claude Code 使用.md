# 如何把這個知識庫交給 Claude Code

> 這個資料夾就是知識庫本體（純文字 Markdown）。
> Claude Code 看不到它，**唯一原因**是：Claude Code 只看得到它「啟動所在的那個資料夾」及其底下的東西。
> 你的知識庫如果還躺在「下載」資料夾、或還是一個沒解壓的 .zip、或 Claude Code 是在別的專案啟動的，它自然看不到。
> 解法就是把這個資料夾放到一個固定位置，然後讓 Claude Code 在那裡啟動。

---

## 路徑 A — 最快：放成 Mac 上的一個資料夾

```bash
# 1. 解壓縮（假設 zip 在下載資料夾）
cd ~/Downloads
unzip 叮噹長壽知識庫.zip -d ~/Documents/

# 2. 進到資料夾
cd ~/Documents/叮噹長壽知識庫

# 3. 在這裡啟動 Claude Code（關鍵就是這一步）
claude
```

現在 Claude Code 的工作目錄就是知識庫，它讀得到全部 45 篇筆記了。
（用桌面版 / Cowork 的話，就把這個資料夾「加進工作區 / 允許的目錄」，效果一樣。）

---

## 路徑 B — 推薦：放進 Git Repo（長期真相來源）

這條路符合我們定的原則：vault 是唯一真相來源、跨裝置、不依賴單一機器或對話。

```bash
# 1. 解壓並進入
unzip ~/Downloads/叮噹長壽知識庫.zip -d ~/Documents/
cd ~/Documents/叮噹長壽知識庫

# 2. 初始化 git
git init
git add .
git commit -m "知識庫初版：9S 為中心、老年醫學為地基（45 篇）"

# 3. 在 GitHub 開一個新 repo（例如 drtingtang-knowledge），然後：
git remote add origin git@github.com:你的帳號/drtingtang-knowledge.git
git branch -M main
git push -u origin main

# 4. 在 repo 目錄啟動 Claude Code
claude
```

之後任何裝置：`git clone` 下來、在裡面開 Claude Code，就是同一個庫。

---

## 重生 HTML 門面

知識庫改完之後，要更新那個 HTML 瀏覽器：

```bash
python3 _tools/產生HTML.py
```

會在資料夾根目錄生出 `叮噹長壽知識庫_瀏覽器.html`，用瀏覽器打開即可。
（這支腳本是「拋棄式衍生視圖」的引擎——永遠改 .md、不要手改 HTML。）

未來若想自動化（你動 .md 它就自動重生），再加一支檔案監看器即可，這是下一步的工程件。

---

## 一句話原則

**地基是這個資料夾，不是任何 app。** Claude Code 負責「寫與連」，HTML 負責「給你看」，
這個資料夾負責「是真相」。把它放進 repo，整套系統就活在你手上、不再依賴任何一次對話。
