# HD Face Swap Cloud Backend

This is an optional cloud-processing path for the Android app. It sends the two selected photos to this backend, which calls the OpenAI Images Edit API and returns a PNG. It is **not offline** and generated results may vary; this is generative editing, not guaranteed pixel-exact identity transfer.

## Security and cost

- Never place `OPENAI_API_KEY` in the APK, `local.properties`, or source control. Configure it as a secret on the backend host.
- Uploaded photos leave the phone and are sent to your backend and the image provider. Only use photos you have permission to process.
- Image API calls may incur charges. Check your API account's model access, organization verification requirements, and current pricing before use.
- Add authentication, rate limits, abuse controls, and request limits before exposing a public service. The sample is a starter, not a hardened public production service.

## Run locally on a PC

1. Install Python 3.11+.
2. In this folder run `python -m venv .venv` and activate it.
3. Run `pip install -r requirements.txt`.
4. Set `OPENAI_API_KEY` in the terminal environment (do not commit it).
5. Run `uvicorn main:app --host 0.0.0.0 --port 8000`.
6. From a physical Android phone on the same Wi-Fi, configure the app's **HD AI Swap (Cloud)** button with `http://<PC-LAN-IP>:8000`. For an Android emulator use `http://10.0.2.2:8000`. HTTP is intended only for local testing.
7. For real use, deploy behind HTTPS and enter the HTTPS URL in the app.

Health check: `GET /health`
Image endpoint: `POST /v1/face-swap` with multipart fields `source_image` and `target_image`.

The app remembers the URL. Clear the app's storage to reset it, or use a fresh app install to enter another URL. The OpenAI API key is configured only on the backend.
