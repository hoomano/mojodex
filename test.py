import requests
website_url = "https://hoomano.com/"

if not website_url.startswith("https://") and not website_url.startswith("http://"):
    website_url = "https://" + website_url
response = requests.get(website_url)
print(response.text)
