# Google OAuth Setup Guide

This guide helps you fix the "error 400: redirect_url_mismatch" issue when authenticating with Google Docs.

## Problem

The error `redirect_url_mismatch` occurs when the redirect URL configured in your Google Cloud Console doesn't match the URL that the application is trying to use for OAuth authentication.

## Solution

### Step 1: Set up Google Cloud Console

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create or select a project**
   - Create a new project or select an existing one

3. **Enable Google Docs API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google Docs API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Desktop application" as the application type
   - Name it (e.g., "Launch Doc Reviewer")

5. **Configure Authorized Redirect URIs**
   - In your OAuth 2.0 Client ID settings, add these redirect URIs:
     ```
     http://localhost:8080
     http://localhost:8080/
     ```
   - If you're using a different port, replace 8080 with your chosen port

6. **Download Credentials**
   - Download the JSON credentials file
   - Save it securely (e.g., as `google_credentials.json`)

### Step 2: Configure the Application

#### Option 1: Using Default Port (8080)
```bash
python -m src.main review \
  --doc "https://docs.google.com/document/d/YOUR_DOC_ID" \
  --requirements requirements.yaml \
  --google-credentials path/to/google_credentials.json
```

#### Option 2: Using Custom Port
If port 8080 is in use, specify a different port:

```bash
python -m src.main review \
  --doc "https://docs.google.com/document/d/YOUR_DOC_ID" \
  --requirements requirements.yaml \
  --google-credentials path/to/google_credentials.json \
  --oauth-port 9090
```

**Important:** If you use a custom port, you must add that port to your Google Cloud Console redirect URIs:
- `http://localhost:9090`
- `http://localhost:9090/`

### Step 3: Environment Variable (Alternative)

Instead of using the `--google-credentials` flag, you can set an environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/google_credentials.json"
```

Then run without the credentials flag:
```bash
python -m src.main review \
  --doc "https://docs.google.com/document/d/YOUR_DOC_ID" \
  --requirements requirements.yaml \
  --oauth-port 8080
```

## Troubleshooting

### Error: Port already in use
If you get an error that the port is in use:

1. **Find what's using the port:**
   ```bash
   lsof -i :8080  # Replace 8080 with your port
   ```

2. **Use a different port:**
   ```bash
   python -m src.main review --oauth-port 9090 ...
   ```

3. **Update Google Cloud Console** with the new port's redirect URIs

### Error: Invalid credentials
- Make sure you downloaded the correct credentials file (OAuth 2.0, not Service Account)
- Verify the file path is correct
- Check that the file has proper read permissions

### Error: Access denied
- Ensure the Google account you're authenticating with has access to the document
- Check that the document URL is correct and publicly accessible or shared with your account

### Error: API not enabled
- Go to Google Cloud Console → APIs & Services → Library
- Enable "Google Docs API" for your project

## Common Redirect URIs

Depending on your setup, you might need these redirect URIs in Google Cloud Console:

```
http://localhost:8080
http://localhost:8080/
http://127.0.0.1:8080
http://127.0.0.1:8080/
```

## Security Notes

1. **Keep credentials secure**: Never commit your `google_credentials.json` to version control
2. **Use environment variables**: For production, use environment variables instead of file paths
3. **Limit scope**: The application only requests `documents.readonly` permission
4. **Token storage**: OAuth tokens are stored in `token.json` for reuse

## Testing the Setup

After configuration, test with a simple command:

```bash
python -m src.main check-setup
```

This will verify your Google credentials are working properly.

## Need Help?

If you're still having issues:

1. Check the detailed error message - it often contains the exact redirect URI that failed
2. Verify your Google Cloud Console settings match exactly
3. Try deleting `token.json` to force re-authentication
4. Ensure your port isn't blocked by firewall or antivirus software