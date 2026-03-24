# Deployment Guide

## API Keys Configuration

### For End Users (No Action Required) ✅
**End users do NOT need to provide API keys.** They simply:
- ✅ Enter course details (title, audience, tone, etc.)
- ✅ Upload documents (optional)
- ✅ Get the generated course output

**That's it!** The app handles everything using server-configured API keys.

### For Developers/Admins (Deployment Setup) 🔧

API keys must be configured as **environment variables** on your deployment platform. The app will automatically use these keys.

#### Required API Keys:
1. `GEMINI_API_KEY` - Google Gemini AI for content generation

#### Deployment Platforms:

##### 1. Heroku
```bash
heroku config:set GEMINI_API_KEY="your-gemini-api-key"
```

##### 2. AWS (Elastic Beanstalk / EC2)
```bash
# Using EB CLI
eb setenv GEMINI_API_KEY="your-key"

# Or in AWS Console: Configuration → Software → Environment properties
```

##### 3. Docker
```dockerfile
# In docker-compose.yml or Dockerfile
ENV GEMINI_API_KEY=your-key
```

##### 4. Local Development (.env file)
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your-gemini-api-key
```

### Security Best Practices

1. **Never commit API keys to Git**
   - `.env` is already in `.gitignore`
   - Never push secrets to GitHub

2. **Use platform-specific secret management**
   - Heroku: Config vars
   - AWS: Secrets Manager or Parameter Store
   - Azure: Key Vault

3. **Rotate keys regularly**
   - Update keys if compromised
   - Use separate keys for dev/staging/production

4. **Monitor API usage**
   - Set up billing alerts
   - Monitor usage in API provider dashboards

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key | - |
| `GEMINI_MODEL` | No | Model to use: `gemini-2.5-pro` or `gemini-2.5-flash` | `gemini-2.5-pro` |
| `PORT` | No | Server port | `8000` |
| `HOST` | No | Server host | `0.0.0.0` |
| `LOG_LEVEL` | No | Logging level | `INFO` |

### Verification

After deployment, verify API keys are loaded:
1. Check application logs for warnings
2. Try generating a course
3. If errors occur, verify keys in deployment platform settings

### User Experience

End users will see:
- ✅ Simple course generation interface
- ✅ No API key input required
- ✅ Direct course output
- ✅ Secure, server-side processing
