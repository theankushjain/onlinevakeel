# **Track B inference API guide**

## *IIT KGP Capstone  \|  5 November 2026*

Your coordinator provides your group API key and the CA certificate listed below. Use your assigned URL to call Qwen3-8B. The certificate verifies the HTTPS service.

# **Your connection details**

The model ID is Qwen/Qwen3-8B for every group. Your key works only on the URL assigned to your group. Keep the key private and share it only within your authorized group.

| Group IDs | API base URL | CA certificate |
| :---: | :---- | :---- |
| 001-015 | https\://103.42.50.41:1031/v1 | vm07-ca.crt |
| 016-030 | https\://103.42.50.41:1032/v1 | vm06-ca.crt |
| 031-045 | https\://103.42.50.41:1033/v1 | vm05-ca.crt |
| 046-065 | https\://103.42.50.41:1034/v1 | vm04-ca.crt |

# **Make your first call**

1\. Save your .crt certificate in Downloads. Extract it if needed. The client needs the exact file path; it does not find the file automatically.

2\. Use your assigned URL and certificate. This example is for groups 046-065. Other groups must use their own row above.

3\. Replace YOUR\_GROUP\_API\_KEY with your own key and run the following command in a macOS or Linux terminal. For another HTTP client, use the same URL, headers and JSON body.

curl \--cacert "\$HOME/Downloads/vm04-ca.crt" \\  
  https\://103.42.50.41:1034/v1/chat/completions \\  
  \-H "Authorization: Bearer YOUR\_GROUP\_API\_KEY" \\  
  \-H "Content-Type: application/json" \\  
  \-d '{  
    "model": "Qwen/Qwen3-8B",  
    "messages": \[  
      {"role": "user", "content": "Explain RAG in three steps."}  
    \],  
    "max\_tokens": 256  
  }' 

Read the answer from choices\[0\].message.content. Change content in your request to ask your own question.

## **Windows PowerShell**

Check your certificate and key using curl.exe and the Windows Downloads path:

curl.exe \--cacert "\$env:USERPROFILE\\Downloads\\vm04-ca.crt" \`  
  \-H "Authorization: Bearer YOUR\_GROUP\_API\_KEY" \`  
  https\://103.42.50.41:1034/v1/models

If you save the certificate in another folder, replace the Downloads path with its actual file path. Keep the path in double quotes, especially when it contains spaces.

The base URL already includes /v1. Append /chat/completions once when making an inference call.

# **Limits and help**

| Setting | Current limit |
| :---- | :---- |
| Active requests per key | 1 across everyone using that group key |
| Requests per key | 60 per minute |
| Combined input and output | 8192 tokens |
| Output length | 512 tokens by default; 1024 maximum per call |
| Shared VM capacity | 15 active requests on VM07, VM06 and VM05; 20 on VM04 |

If two learners use the same key at the same time, the first request continues and the second receives 429\. Wait for the first answer to finish, or queue requests in your application. Other group keys can still work while capacity is available.

# **Common errors**

| Result | What to do |
| :---- | :---- |
| 401 Unauthorized | Check your key and assigned URL. Include Authorization: Bearer followed by your key. |
| 429 Too Many Requests | Wait for the active request to finish or for the rate limit to recover, then retry. |
| 503 Service Unavailable | The VM may be busy or the model may not be ready. Wait and retry a limited number of times. |
| 400 Bad Request | Check the JSON, model ID and context length. Set max\_tokens between 1 and 1024\. |
| 404 Not Found | Check the path. Use /v1/chat/completions; do not repeat /v1. |
| Certificate error | Use the matching CA certificate from your coordinator and keep HTTPS verification enabled. |

For temporary 429 or 503 errors, retry with increasing delays, such as 2, 4 and 8 seconds. Stop after the retry limit and report persistent failures.

# **Using the API in your project**

The API supports chat responses, streaming and tool-call responses. Your application handles tool execution, document retrieval and conversation history. Embeddings are not provided on these endpoints; a RAG project needs a separate embeddings service.

# **Get help**

Send your coordinator your group ID, API URL, error code, and the time of the problem. Remove your key from request examples and screenshots. If the key was exposed, ask for a replacement.