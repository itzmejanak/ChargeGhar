# 🔥 AI Implementation Guide – Cloud Upload Services

We need to **verify and implement dual cloud upload services** (Cloudinary + AWS S3), controlled dynamically via the `AppConfig` model flag.

Follow these instructions **step by step, without skipping anything**. The implementation must be **production ready, reliable, and maintainable**.

---

## 📌 Requirements

1. **Upload Providers**

   * Cloudinary
   * AWS S3
     (Both must be implemented and switchable.)

2. **Configuration**

   * Use `.env` for all secrets (AWS + Cloudinary).

3. **Switching Provider**

   * Controlled by `AppConfig` model (via admin panel).
   * Admin can change the provider dynamically without code changes.
   * Factory/service pattern must be used.

4. **Cleanup**

   * Delete or refactor any old/local upload logic.
   * Keep code modular, organized, and easy to maintain.
   * Ensure folder structure is followed.

---

## 📂 Implementation Plan

### 1. **Service Layer**

* Create an abstract `CloudStorageService`.
* Implement:

  * `CloudinaryService`
  * `S3Service`

### 2. **Factory**

* Implement `CloudStorageFactory` that:

  * Reads from `AppConfig` + `.env`.
  * Returns correct provider service.
  * Has safe fallback mechanism.

### 3. **Configuration**

* Create `CloudStorageConfigService` to:

  * Validate provider.
  * Handle errors.
  * Ensure correct setup.

### 4. **Media Upload Service**

* Replace all local upload logic.
* Integrate cloud storage via factory.
* Store cloud metadata in DB (provider, public\_id, URL, etc.).
* Ensure strong error handling + logging.

### 5. **Database Model**

* `MediaUpload` model should:

  * Have `metadata` JSONField.
  * Store provider info, public\_id, etc.

### 6. **Admin**

* Extend `AppConfig` in Django admin.
* Allow switching providers with validation.
* Clear cache after change.

### 7. **Management Command**

* `setup_cloud_storage` command to:

  * Set provider (cloudinary/s3).
  * Validate keys.
  * Report status.

### 8. **Background Tasks**

* Add cleanup jobs for orphaned files.
* Ensure proper cleanup and updated logic.

---

## ✅ Success Criteria

* No local upload code remains.
* Cloudinary = default provider.
* AWS S3 = secondary provider.
* Switching providers works via admin.
* All secrets in `.env`.
* Background cleanup tasks functional.
* Code is modular, maintainable, and production-ready.

---

⚡ **Final Instruction for AI**:

> Implement the above cloud upload architecture exactly as described.
> Follow step-by-step, clean old code, keep it production-ready, reliable, and maintainable.
> Always validate configuration, handle errors, and respect the folder structure.

---