INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES
    ('pet-photos', 'pet-photos', TRUE, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp']),
    ('chat-attachments', 'chat-attachments', FALSE, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp']),
    ('avatars', 'avatars', TRUE, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

CREATE POLICY "public can read pet photos"
ON storage.objects FOR SELECT
USING (bucket_id = 'pet-photos');

CREATE POLICY "authenticated users can upload pet photos"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'pet-photos' AND auth.role() = 'authenticated');

CREATE POLICY "chat attachments require authentication"
ON storage.objects FOR SELECT
USING (bucket_id = 'chat-attachments' AND auth.role() = 'authenticated');

CREATE POLICY "authenticated users can upload chat attachments"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'chat-attachments' AND auth.role() = 'authenticated');

CREATE POLICY "public can read avatars"
ON storage.objects FOR SELECT
USING (bucket_id = 'avatars');

CREATE POLICY "users can upload own avatar"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'avatars'
    AND auth.role() = 'authenticated'
    AND (storage.foldername(name))[1] = auth.uid()::TEXT
);
