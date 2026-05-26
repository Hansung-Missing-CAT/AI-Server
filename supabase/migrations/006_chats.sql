CREATE TABLE IF NOT EXISTS public.chats (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id          UUID REFERENCES public.missing_pets(id) ON DELETE SET NULL,
    participant_ids UUID[] NOT NULL,
    last_message    TEXT,
    last_message_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id    UUID NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
    sender_id  UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    type       TEXT NOT NULL DEFAULT 'text' CHECK (type IN ('text', 'image', 'location', 'tipCard')),
    message    TEXT,
    image_url  TEXT,
    latitude   DOUBLE PRECISION,
    longitude  DOUBLE PRECISION,
    payload    JSONB,
    read_by    UUID[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chats_participants ON public.chats USING GIN (participant_ids);
CREATE INDEX IF NOT EXISTS idx_chats_last_message_at ON public.chats(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_created ON public.chat_messages(chat_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender ON public.chat_messages(sender_id);

CREATE OR REPLACE FUNCTION public.sync_chat_last_message()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.chats
    SET last_message = COALESCE(NEW.message, NEW.type),
        last_message_at = NEW.created_at
    WHERE id = NEW.chat_id;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS sync_chat_last_message_after_insert ON public.chat_messages;
CREATE TRIGGER sync_chat_last_message_after_insert
AFTER INSERT ON public.chat_messages
FOR EACH ROW EXECUTE FUNCTION public.sync_chat_last_message();
