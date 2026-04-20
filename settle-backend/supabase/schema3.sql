-- ============================================================
-- FUNCTION: seal_agreement_confirm
-- Atomically logs the counterparty confirmation and seals the
-- agreement in a single transaction. Called via supabase.rpc().
-- SECURITY DEFINER runs as the function owner (service role),
-- so it can write to both tables regardless of RLS.
-- ============================================================
CREATE OR REPLACE FUNCTION public.seal_agreement_confirm(
    p_agreement_id  uuid,
    p_user_id       uuid,
    p_seal_hash     text,
    p_seal_payload  jsonb,
    p_sealed_at     timestamptz
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Log counterparty confirmation
    INSERT INTO confirmations (agreement_id, user_id)
    VALUES (p_agreement_id, p_user_id);

    -- Seal the agreement
    UPDATE agreements
    SET
        status             = 'active',
        counterparty_id    = p_user_id,
        seal_hash          = p_seal_hash,
        seal_payload       = p_seal_payload,
        sealed_at          = p_sealed_at,
        confirmation_token = NULL,
        token_expires_at   = NULL
    WHERE id = p_agreement_id;

    -- Guard: if the UPDATE matched nothing, something is wrong — abort
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Agreement % not found during seal', p_agreement_id;
    END IF;
END;
$$;
