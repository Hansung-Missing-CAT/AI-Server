ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.missing_pets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pet_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tips ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pet_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pet_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.breed_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.districts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users can read own profile" ON public.users
FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users can update own profile" ON public.users
FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

CREATE POLICY "missing pets are publicly readable" ON public.missing_pets
FOR SELECT USING (TRUE);

CREATE POLICY "authenticated users can create missing pets" ON public.missing_pets
FOR INSERT WITH CHECK (auth.uid() = reporter_id);

CREATE POLICY "reporters can update missing pets" ON public.missing_pets
FOR UPDATE USING (auth.uid() = reporter_id) WITH CHECK (auth.uid() = reporter_id);

CREATE POLICY "reporters can delete missing pets" ON public.missing_pets
FOR DELETE USING (auth.uid() = reporter_id);

CREATE POLICY "users can manage own tips" ON public.tips
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "participants can manage chats" ON public.chats
FOR ALL USING (auth.uid() = ANY(participant_ids)) WITH CHECK (auth.uid() = ANY(participant_ids));

CREATE POLICY "participants can manage chat messages" ON public.chat_messages
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.chats
        WHERE chats.id = chat_messages.chat_id
          AND auth.uid() = ANY(chats.participant_ids)
    )
) WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.chats
        WHERE chats.id = chat_messages.chat_id
          AND auth.uid() = ANY(chats.participant_ids)
    )
);

CREATE POLICY "users can manage own notifications" ON public.notifications
FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "pet likes are publicly readable" ON public.pet_likes
FOR SELECT USING (TRUE);

CREATE POLICY "authenticated users can like" ON public.pet_likes
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users can unlike own likes" ON public.pet_likes
FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "pet comments are publicly readable" ON public.pet_comments
FOR SELECT USING (TRUE);

CREATE POLICY "authenticated users can comment" ON public.pet_comments
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "users can delete own comments" ON public.pet_comments
FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "breed mapping is publicly readable" ON public.breed_mapping
FOR SELECT USING (TRUE);

CREATE POLICY "districts are publicly readable" ON public.districts
FOR SELECT USING (TRUE);
