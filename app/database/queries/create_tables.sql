CREATE TABLE "chats" (
  "id" varchar PRIMARY KEY,
  "username" varchar,
  "first_name" varchar,
  "ts" time NOT NULL
);

CREATE TABLE "classes" (
  "id" uuid PRIMARY KEY,
  "name" varchar NOT NULL,
  "class_id" varchar NOT NULL,
  "semester" varchar
);

CREATE TABLE "absences" (
  "chat_id" varchar,
  "class_id" uuid,
  "counter" int
);

ALTER TABLE "absences" ADD FOREIGN KEY ("chat_id") REFERENCES "chats" ("id");

ALTER TABLE "absences" ADD FOREIGN KEY ("class_id") REFERENCES "classes" ("id");