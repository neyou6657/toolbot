// Cloudflare Worker script to proxy Telegram API requests
// This script intercepts requests to the Telegram Bot API and forwards them
// allowing your bot to work even when direct access to api.telegram.org is blocked

export default {
    async fetch(request, env, ctx) {
        // Get the original request URL
        const originalUrl = new URL(request.url);

        // Handle CORS preflight requests
        if (request.method === 'OPTIONS') {
            return new Response(null, {
                headers: {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
            });
        }

        // Check if this is a request to our worker
        // If the path starts with /telegram-api, forward to Telegram API
        if (originalUrl.pathname.startsWith('/telegram-api')) {
            // Extract the path after /telegram-api
            // The full path should be like /telegram-api/bot{TOKEN}/{METHOD}
            const telegramApiPath = originalUrl.pathname.replace('/telegram-api', '');

            // Construct the target URL for Telegram API
            const telegramApiUrl = `https://api.telegram.org${telegramApiPath}`;

            // Clone the original request to modify it
            // Remove the Cloudflare-specific headers that might cause issues
            const newHeaders = new Headers(request.headers);
            newHeaders.delete('cf-ray');
            newHeaders.delete('cf-connecting-ip');
            newHeaders.delete('x-forwarded-for');

            const modifiedRequest = new Request(telegramApiUrl, {
                method: request.method,
                headers: newHeaders,
                body: request.body,
                redirect: 'follow'
            });

            try {
                // Send request to Telegram API
                const response = await fetch(modifiedRequest);

                // Return the response from Telegram API with CORS headers
                const modifiedResponse = new Response(response.body, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: {
                        ...response.headers,
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    }
                });

                return modifiedResponse;
            } catch (error) {
                console.error('Proxy error:', error);
                return new Response(JSON.stringify({
                    error: 'Proxy error',
                    details: error.message,
                    message: 'Failed to connect to Telegram API'
                }), {
                    status: 502, // Bad Gateway
                    headers: {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                    }
                });
            }
        }

        // If not a Telegram API request, return info about the proxy
        return new Response('Telegram API Proxy Worker - Ready to forward requests to Telegram API', {
            status: 200,
            headers: {
                'Content-Type': 'text/plain',
                'Access-Control-Allow-Origin': '*',
            }
        });
    }
};