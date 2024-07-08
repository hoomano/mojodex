

import requests

client_id = "441300db6193087bf424c6313e5c69ea"
client_secret="09deef9539d8989e8a03f54cb383903c"

def get_access_token(client_id, client_secret):
    url = "https://auth-sandbox.euipo.europa.eu/oidc/accessToken"
    payload = f"client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials&scope=uid"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


response = get_access_token(client_id, client_secret)
token = response["access_token"]

#token = """eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsIm9yZy5hcGVyZW8uY2FzLnNlcnZpY2VzLlJlZ2lzdGVyZWRTZXJ2aWNlIjoiMTcxMzk3MDE5NTgwOSJ9.eyJzdWIiOiI0NDEzMDBkYjYxOTMwODdiZjQyNGM2MzEzZTVjNjllYSIsImluc3RhbmNlIjoiXC9kZXRhaWxzIiwib2F1dGhDbGllbnRJZCI6IjQ0MTMwMGRiNjE5MzA4N2JmNDI0YzYzMTNlNWM2OWVhIiwicm9sZXMiOltdLCJpc3MiOiJodHRwczpcL1wvYXV0aC1zYW5kYm94LmV1aXBvLmV1cm9wYS5ldVwvdFwvZXVpcG8uZXVyb3BhLmV1XC9vYXV0aDJcL3Rva2VuIiwidGl0bGUiOiJHZW5lcmFsIGVycm9yIiwidHlwZSI6IlwvcHJvYmxlbXNcL2dlbmVyYWwtZXJyb3IiLCJub25jZSI6IiIsImNsaWVudF9pZCI6IjQ0MTMwMGRiNjE5MzA4N2JmNDI0YzYzMTNlNWM2OWVhIiwiYXVkIjoiNDQxMzAwZGI2MTkzMDg3YmY0MjRjNjMxM2U1YzY5ZWEiLCJncmFudF90eXBlIjoiQ0xJRU5UX0NSRURFTlRJQUxTIiwicGVybWlzc2lvbnMiOltdLCJzY29wZSI6InVpZCIsImNsYWltcyI6W10sInNjb3BlcyI6InVpZCIsInN0YXRlIjoiIiwiZGV0YWlsIjoicG9ydGFsLXdzIHNlcnZpY2UgZXJyb3I6IE5vdCBGb3VuZCIsImV4cCI6MTcxNDA2MDQyMywiaWF0IjoxNzE0MDMxNjIzLCJqdGkiOiJBVC0yNDk5OS1LdGNJcjVYeXdZaG85LTlKc1hrMU9CT21tVzcyZ3Z1ZSIsInN0YXR1cyI6NTAwfQ.jvLLqZcalc6mdMj3PQZlL1hI3feIZ4ZWyou71cEsrbSolyFI07skSfINUiiPwN342_HuRHQqOpYOn3IZNrv-HmJMtFANHXehCNJUMD7ma5mtDt1WXQpYkHQUSq1UqZD6S9bO9X_KRTq0_hb_VEtHQSsfiUohhHs8ExV5qwGls1bHiEW6hCk6JWR_N79pekNqs0T0BcjYOwEM6wtDeo3w80SZtJSzED3tfaCrHsES2ZpXOko-RQaxafrA0ts6wQCiGvtGrRv2QIsVa0g0AmY-l4Cvm3VacHfrvmwN0VWK_cvhhef5R6bqRz2HDuCqD1yaa537xkEOk9mxRvKxl5OWvQ"""

def _validate_keywords_hdb_matching():
    payload = {
        "sourceLanguage": "fr",
        "goodsAndServices": [{
            "classNumber": 42,
            "terms": ["Analyse de systèmes informatiques", " Consultation en technologie de l'information", " Maintenance de logiciels informatiques", " Mise à jour de logiciels informatiques", " Services d'assistants virtuels pour la gestion de tâches personnelles", " Services de conception de logiciels", " Services de conception de systèmes informatiques", " Services de conseil en conception de logiciels", " Services de conseil en matière d'ordinateurs", " Services de conseil en propriété intellectuelle.", " Services de conseillers en technologie de l'information", " Services de développement de logiciels d'intelligence artificielle", " Services de recherche et développement de nouveaux produits pour des tiers"]
        }]
    }
    headers = {
        "X-IBM-Client-Id": client_id,
        "Authorization": f"Bearer {token}"
        }

    # call Harmonized Database API
    response = requests.post("https://api-sandbox.euipo.europa.eu/goods-and-services/classification-validation", 
                                json=payload, headers=headers)
    
    json_response = response.json()
    return json_response

response = _validate_keywords_hdb_matching()
print(response)
exit()
def suggest_terms():
    payload = {"language": "fr",
        "texts":  ["Logiciels en tant que service (saas) pour services de propriété intellectuelle"]}#["Financieel advies", "Financi\u00eble consultancy", 
                  # "Financi\u00eble informatie", "Financi\u00eble evaluaties", 
                  # "Financi\u00eble planning", "Vermogensbeheer", "Beleggingsadvies", 
                  # "Ontwikkeling van software", "Ontwerp en ontwikkeling van computersoftware",                                                                                                                                                                                                                              
                   #  "Computerprogrammering", 
                     #"Onderhoud van software", "Actualisering van computer software", "Computer software consultancy"
                    # ]}
    headers = {
        "X-IBM-Client-Id": client_id,
        "Authorization": f"Bearer {token}"
        }

    # call Harmonized Database API
    response = requests.post("https://api-sandbox.euipo.europa.eu/goods-and-services/terms-suggestion-list", 
                                json=payload, headers=headers)
  
    
    json_response = response.json()
    return json_response

response = suggest_terms()
print(response)
            
   
    



    


print(response)