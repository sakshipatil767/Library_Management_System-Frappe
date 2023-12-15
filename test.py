import requests

dic = {}
for i in range(1,36):

    url = "https://frappe.io/api/method/frappe-library"
    params = {
        "page": i,
        "title": "and"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  
        data = response.json()
        dic[i] = data["message"]
        print(i,"data added...")  
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    
print(dic)