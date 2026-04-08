-- ============================================================
-- SETTLE APP — SUPABASE DATABASE SCHEMA
-- Run this in the Supabase SQL editor
-- ============================================================


-- ============================================================
-- TABLE: profiles
-- ============================================================
CREATE TABLE profiles (
    id          uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    phone_number text UNIQUE NOT NULL,
    full_name   text,
    created_at  timestamptz DEFAULT now()
);

-- RLS: profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);


-- ============================================================
-- TABLE: agreements
-- ============================================================
CREATE TABLE agreements (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title                text NOT NULL,
    amount               numeric(12, 2) NOT NULL,
    terms                text NOT NULL,
    initiator_id         uuid NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    counterparty_id      uuid REFERENCES profiles(id) ON DELETE RESTRICT,
    counterparty_phone   text NOT NULL,
    repayment_date       date NOT NULL,
    status               text NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending', 'active', 'completed', 'overdue', 'cancelled')),
    seal_hash            text,
    seal_payload         jsonb,
    sealed_at            timestamptz,
    confirmation_token   text UNIQUE,
    token_expires_at     timestamptz,
    created_at           timestamptz DEFAULT now()
);

-- RLS: agreements
ALTER TABLE agreements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Initiator can view own agreements"
    ON agreements FOR SELECT
    USING (auth.uid() = initiator_id);

CREATE POLICY "Counterparty can view agreements they are party to"
    ON agreements FOR SELECT
    USING (auth.uid() = counterparty_id);

CREATE POLICY "Initiator can insert agreements"
    ON agreements FOR INSERT
    WITH CHECK (auth.uid() = initiator_id);

CREATE POLICY "Initiator can update own agreements"
    ON agreements FOR UPDATE
    USING (auth.uid() = initiator_id);

-- Indexes: agreements
CREATE INDEX idx_agreements_initiator_id       ON agreements(initiator_id);
CREATE INDEX idx_agreements_counterparty_id    ON agreements(counterparty_id);
CREATE INDEX idx_agreements_status             ON agreements(status);
CREATE INDEX idx_agreements_confirmation_token ON agreements(confirmation_token);


-- ============================================================
-- TABLE: confirmations
-- ============================================================
CREATE TABLE confirmations (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_id  uuid NOT NULL REFERENCES agreements(id) ON DELETE CASCADE,
    user_id       uuid NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    confirmed_at  timestamptz DEFAULT now(),
    ip_address    text
);

-- RLS: confirmations
ALTER TABLE confirmations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Initiator can view confirmations on their agreements"
    ON confirmations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM agreements
            WHERE agreements.id = confirmations.agreement_id
              AND agreements.initiator_id = auth.uid()
        )
    );

CREATE POLICY "Counterparty can view confirmations on their agreements"
    ON confirmations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM agreements
            WHERE agreements.id = confirmations.agreement_id
              AND agreements.counterparty_id = auth.uid()
        )
    );

CREATE POLICY "Authenticated users can insert own confirmation"
    ON confirmations FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- ============================================================
-- TABLE: payments
-- ============================================================
CREATE TABLE payments (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_id            uuid NOT NULL REFERENCES agreements(id) ON DELETE CASCADE,
    payer_id                uuid NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    amount                  numeric(12, 2) NOT NULL,
    note                    text,
    logged_at               timestamptz DEFAULT now(),
    confirmed_by_receiver   boolean DEFAULT false,
    confirmed_at            timestamptz
);

-- RLS: payments
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Initiator can view payments on their agreements"
    ON payments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM agreements
            WHERE agreements.id = payments.agreement_id
              AND agreements.initiator_id = auth.uid()
        )
    );

CREATE POLICY "Counterparty can view payments on their agreements"
    ON payments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM agreements
            WHERE agreements.id = payments.agreement_id
              AND agreements.counterparty_id = auth.uid()
        )
    );

CREATE POLICY "Payer can insert own payments"
    ON payments FOR INSERT
    WITH CHECK (auth.uid() = payer_id);

CREATE POLICY "Parties can update payment confirmation"
    ON payments FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM agreements
            WHERE agreements.id = payments.agreement_id
              AND (agreements.initiator_id = auth.uid() OR agreements.counterparty_id = auth.uid())
        )
    );

-- Indexes: payments
CREATE INDEX idx_payments_agreement_id ON payments(agreement_id);


-- ============================================================
-- TABLE: notifications
-- ============================================================
CREATE TABLE notifications (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    agreement_id  uuid REFERENCES agreements(id) ON DELETE SET NULL,
    type          text NOT NULL,
    channel       text NOT NULL,
    status        text NOT NULL DEFAULT 'sent',
    sent_at       timestamptz DEFAULT now()
);

-- RLS: notifications
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own notifications"
    ON notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service can insert notifications"
    ON notifications FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Indexes: notifications
CREATE INDEX idx_notifications_user_id ON notifications(user_id);


-- ============================================================
-- FUNCTION: auto-create profile on signup
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, phone_number)
    VALUES (
        NEW.id,
        COALESCE(NEW.phone, NEW.raw_user_meta_data->>'phone_number')
    );
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
