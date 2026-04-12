# Developing in GitHub Codespaces

GitHub Codespaces provides a fully-featured cloud development environment specifically tailored to this repository. You can use it to test Docker compilations, fix Python dependency issues, and run the FastAPI server entirely in your browser without needing to deploy to Cloud Run!

## 🚀 Getting Started

1. Navigate to the `<> Code` button at the top right of the GitHub repository.
2. Switch to the **Codespaces** tab.
3. Click the **`+`** button to spin up a new Codespace on your branch (e.g., `faisal-alltrack`).
4. Wait a few seconds for the Ubuntu Linux environment to provision.

## 🛠️ Testing Your Docker Pipeline

Because GitHub Actions (which runs Ubuntu) operates identically to Codespaces, it is the absolute best place to test why a feature like `pip install` or `docker build` fails in the CI pipeline.

To execute a test build, open the terminal in your Codespace (`` Ctrl+` ``) and run:
```bash
docker build --progress=plain -t test_workorch .
```
*The `--progress=plain` flag is critical because it forces Docker to dump the exact crash stacktraces on the screen without truncating them!*

## 🌐 Running Your App Live

Once your container successfully compiles, you can execute the server live:
```bash
docker run -p 8080:8080 -e PORT=8080 test_workorch
```

**Port Forwarding:**
When the container binds to port 8080, GitHub Codespaces will automatically detect the active port. A small pop-up will appear in the bottom right corner reading **"Open in Browser"**.
Clicking this auto-generates a secure tunnel straight to your instance, meaning you can test your APIs natively from anywhere!

## 🔐 Environment Variables (.env)

If your code crashes internally because it cannot hit the AlloyDB database or is missing the Google API Key:
1. Codespaces are empty by default—they don't contain your `.env` file because it is ignored by `.gitignore`.
2. To test application features deeper than just the Docker compilation, recreate your `.env` file in the root `.workspace/` and paste your secrets.
3. Be sure to use the **Local Application Proxy IP** (`ALLOYDB_HOST=127.0.0.1`) just like you do on your personal machine!
