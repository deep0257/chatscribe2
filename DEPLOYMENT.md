# ChatScribe Deployment Guide

## Deploying to Render

### Prerequisites
- GitHub repository with your code
- Render account (logged in)
- Environment variables configured

### Manual Deployment Steps

1. **Push code to GitHub** (fix authentication first if needed):
   ```bash
   # Option A: Use SSH
   git remote set-url origin git@github.com:deep0257/chatscribe.git
   
   # Option B: Use Personal Access Token
   # Generate token from GitHub Settings → Developer settings → Personal access tokens
   ```

2. **Create Web Service on Render**:
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect GitHub repository: `https://github.com/deep0257/chatscribe.git`
   - Configure:
     - Name: `chatscribe`
     - Environment: `Python 3`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python start.py`

3. **Set Environment Variables**:
   ```
   DATABASE_URL=<your-postgresql-url>
   SECRET_KEY=<secure-secret-key>
   PINECONE_API_KEY=<your-pinecone-key>
   PINECONE_ENVIRONMENT=<pinecone-environment>
   PINECONE_INDEX_NAME=<pinecone-index-name>
   OPENAI_API_KEY=<your-openai-key>
   ```

4. **Create PostgreSQL Database** (if needed):
   - Dashboard → New + → PostgreSQL
   - Copy External Database URL
   - Use as DATABASE_URL environment variable

5. **Deploy**:
   - Click "Create Web Service"
   - Wait for build and deployment to complete
   - Your app will be available at the provided Render URL

### Files Added for Deployment
- `render.yaml` - Render service configuration
- `start.py` - Production startup script
- `DEPLOYMENT.md` - This deployment guide

### Troubleshooting
- Check build logs in Render dashboard
- Verify all environment variables are set
- Ensure database is accessible
- Check application logs for runtime errors
