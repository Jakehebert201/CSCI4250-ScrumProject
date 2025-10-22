# OAuth Setup Guide

This guide will help you set up Google OAuth for the Student Tracker application.

## Prerequisites

1. A Google account
2. Access to Google Cloud Console

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: "Student Tracker" (or your preferred name)
4. Click "Create"

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API" and enable it
3. Also enable "Google Identity" if available

## Step 3: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" for user type
   - Fill in required fields:
     - App name: "Student Tracker"
     - User support email: your email
     - Developer contact: your email
   - Add scopes: `email`, `profile`, `openid`
   - Add test users if needed

4. For OAuth client ID:
   - Application type: "Web application"
   - Name: "Student Tracker Web Client"
   - Authorized redirect URIs: 
     - `http://localhost:5000/oauth/callback` (for development)
     - `https://yourdomain.com/oauth/callback` (for production)

## Step 4: Configure Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   FLASK_SECRET=your-super-secret-key-here
   ```

## Step 5: Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 6: Run the Application

```bash
python app.py
```

## Testing OAuth

1. Go to `http://localhost:5000`
2. Click "Get Started"
3. Try the "Student (Google)" or "Professor (Google)" buttons
4. You should be redirected to Google's login page
5. After successful authentication, you'll be redirected back to the app

## Security Notes

- Never commit your `.env` file to version control
- Use strong, unique secrets for production
- Configure proper redirect URIs for your production domain
- Consider using environment-specific OAuth applications (dev, staging, prod)

## Troubleshooting

### "redirect_uri_mismatch" error
- Check that your redirect URI in Google Console matches exactly: `http://localhost:5000/oauth/callback`
- Make sure there are no trailing slashes or extra characters

### "invalid_client" error
- Verify your client ID and secret are correct in `.env`
- Make sure the OAuth client is enabled in Google Console

### "access_denied" error
- Check OAuth consent screen configuration
- Ensure your email is added as a test user if the app is not published

## Production Deployment

For production:
1. Update redirect URIs in Google Console to use your production domain
2. Set proper environment variables on your server
3. Use HTTPS for all OAuth redirects
4. Consider publishing your OAuth consent screen for public use