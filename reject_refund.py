import requests
import json

# Get token
response = requests.post('http://api:80/api/users/login/', json={
    'identifier': 'admin@example.com',
    'password': 'password'
})
print(response.text)

# Reject refund
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}
data = {
    'refund_id': 'a64a43f5-cf14-41be-acc4-3285603a27ba',
    'rejection_reason': 'some_reason'
}
response = requests.post('http://api:80/api/admin/refunds/reject', headers=headers, json=data)

print(response.json())