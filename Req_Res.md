# **🔌 <App_name> API Specification Template**

## **\[Feature Name]**

### **Endpoint**

`[METHOD] /api/...`

### **Description**

`[Short explanation of what this endpoint does]`

---

### **Request**

**Headers**

```json
{
  "Authorization": "Bearer <token>",   // If authentication is required
  "Content-Type": "application/json"
}
```

**Query Parameters (if any)**

```json
{
  "key": "value"
}
```

**Request Body (if any)**

```json
{
  "field1": "string",
  "field2": "number|boolean|object"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // response fields here
  }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message"
  }
}
```