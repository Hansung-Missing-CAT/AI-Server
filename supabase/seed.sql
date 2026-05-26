INSERT INTO public.breed_mapping (cat_api_name, kr_name) VALUES
('Abyssinian', '아비시니안'),
('Aegean', '에게안'),
('American Bobtail', '아메리칸 밥테일'),
('American Curl', '아메리칸 컬'),
('American Shorthair', '아메리칸 숏헤어'),
('Bengal', '벵갈'),
('Birman', '버만'),
('Bombay', '봄베이'),
('British Shorthair', '브리티시 숏헤어'),
('Burmese', '버미즈'),
('Chartreux', '샤르트뢰'),
('Cornish Rex', '코니시 렉스'),
('Devon Rex', '데본 렉스'),
('Egyptian Mau', '이집션 마우'),
('Exotic Shorthair', '엑조틱 숏헤어'),
('Maine Coon', '메인쿤'),
('Norwegian Forest Cat', '노르웨이 숲'),
('Persian', '페르시안'),
('Ragdoll', '랙돌'),
('Russian Blue', '러시안 블루'),
('Scottish Fold', '스코티시 폴드'),
('Siamese', '샴'),
('Siberian', '시베리안'),
('Sphynx', '스핑크스'),
('Turkish Angora', '터키시 앙고라')
ON CONFLICT (cat_api_name) DO UPDATE SET kr_name = EXCLUDED.kr_name;

INSERT INTO public.districts (name) VALUES
('강남구'),
('강동구'),
('강북구'),
('강서구'),
('관악구'),
('광진구'),
('마포구'),
('서초구'),
('송파구')
ON CONFLICT (name) DO NOTHING;
