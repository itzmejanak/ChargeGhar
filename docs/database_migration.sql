-- Nepal Gateways Integration Database Migration Script
-- This script updates the database to support nepal-gateways integration

-- Remove Stripe payment methods
DELETE FROM payment_methods WHERE gateway = 'stripe';

-- Clean up any Stripe webhook records
DELETE FROM payment_webhooks WHERE gateway = 'stripe';

-- Update eSewa payment method (if exists)
UPDATE payment_methods 
SET configuration = jsonb_build_object(
    'use_env_config', true,
    'env_prefix', 'ESEWA'
)
WHERE gateway = 'esewa';

-- Update Khalti payment method (if exists)
UPDATE payment_methods 
SET configuration = jsonb_build_object(
    'use_env_config', true,
    'env_prefix', 'KHALTI'
)
WHERE gateway = 'khalti';

-- Insert default eSewa payment method if it doesn't exist
INSERT INTO payment_methods (id, name, gateway, is_active, min_amount, max_amount, supported_currencies, configuration, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'eSewa',
    'esewa',
    true,
    50.00,
    50000.00,
    '["NPR"]'::jsonb,
    jsonb_build_object('use_env_config', true, 'env_prefix', 'ESEWA'),
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM payment_methods WHERE gateway = 'esewa');

-- Insert default Khalti payment method if it doesn't exist
INSERT INTO payment_methods (id, name, gateway, is_active, min_amount, max_amount, supported_currencies, configuration, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'Khalti',
    'khalti',
    true,
    10.00,
    100000.00,
    '["NPR"]'::jsonb,
    jsonb_build_object('use_env_config', true, 'env_prefix', 'KHALTI'),
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM payment_methods WHERE gateway = 'khalti');

-- Clean up any failed Stripe transactions (optional)
-- UPDATE transactions SET status = 'CANCELLED' WHERE payment_method_type = 'GATEWAY' AND gateway_reference LIKE 'stripe_%' AND status = 'PENDING';

-- Verify the changes
SELECT 'Payment Methods After Migration:' as info;
SELECT id, name, gateway, is_active, min_amount, max_amount FROM payment_methods WHERE gateway IN ('esewa', 'khalti');

SELECT 'Webhook Records After Cleanup:' as info;
SELECT COUNT(*) as remaining_webhooks, gateway FROM payment_webhooks GROUP BY gateway;