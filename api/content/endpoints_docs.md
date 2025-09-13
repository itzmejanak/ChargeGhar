# **🔌 ChargeGhar Content API Specification**

## **Admin Endpoints**

## **AdminContentPagesView API**

### **Endpoint**

`PUT /api/admin/content/pages`

### **Description**

Admin content pages management endpoint

---

### **Request**

**Headers**

```json
{
  "Content-Type": "application/json"
}
```

**Request Body**

```json
{
  "field1": "string",
  "field2": "value"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
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

---

## **AdminContentAnalyticsView API**

### **Endpoint**

`GET /api/admin/content/analytics`

### **Description**

Admin content analytics endpoint

---

### **Request**

**Headers**

```json
{
  "Content-Type": "application/json"
}
```

---

### **Response**

**Success**

```json
{
  "success": true,
  "data": {
    // Response data
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

---

## **Common Error Codes**

| Error Code | Description |
|------------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `UNAUTHORIZED` | Authentication required |
| `PERMISSION_DENIED` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
