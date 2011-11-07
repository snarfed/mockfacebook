-- Do not edit! Generated automatically by mockfacebook.
-- http://code.google.com/p/mockfacebook/
-- 2011-11-07 13:54:37.125627


CREATE TABLE `album` (
  aid TEXT,
  object_id INTEGER,
  owner INTEGER,
  cover_pid TEXT,
  cover_object_id TEXT,
  name TEXT,
  created INTEGER,
  modified INTEGER,
  description TEXT,
  location TEXT,
  size INTEGER,
  link TEXT,
  visible TEXT,
  modified_major INTEGER,
  edit_link TEXT,
  type TEXT,
  can_upload INTEGER,
  photo_count INTEGER,
  video_count INTEGER
);

CREATE TABLE `application` (
  app_id TEXT,
  api_key TEXT,
  canvas_name TEXT,
  display_name TEXT,
  icon_url TEXT,
  logo_url TEXT,
  company_name TEXT,
  developers ,
  description TEXT,
  daily_active_users TEXT,
  weekly_active_users TEXT,
  monthly_active_users TEXT,
  category TEXT,
  subcategory TEXT,
  is_facebook_app INTEGER,
  restriction_info 
);

CREATE TABLE `apprequest` (
  request_id TEXT,
  app_id TEXT,
  recipient_uid TEXT,
  sender_uid TEXT,
  message TEXT,
  data TEXT,
  created_time INTEGER
);

CREATE TABLE `checkin` (
  checkin_id INTEGER,
  author_uid INTEGER,
  page_id INTEGER,
  app_id INTEGER,
  post_id INTEGER,
  coords ,
  timestamp INTEGER,
  tagged_uids ,
  message TEXT
);

CREATE TABLE `comment` (
  xid TEXT,
  object_id INTEGER,
  post_id TEXT,
  fromid INTEGER,
  time INTEGER,
  text TEXT,
  id TEXT,
  username TEXT,
  reply_xid TEXT,
  post_fbid TEXT,
  app_id INTEGER,
  likes INTEGER,
  comments ,
  user_likes INTEGER,
  is_private INTEGER
);

CREATE TABLE `comments_info` (
  app_id TEXT,
  xid TEXT,
  count INTEGER,
  updated_time INTEGER
);

CREATE TABLE `connection` (
  source_id INTEGER,
  target_id INTEGER,
  target_type TEXT,
  is_following INTEGER
);

CREATE TABLE `cookies` (
  uid TEXT,
  name TEXT,
  value TEXT,
  expires INTEGER,
  path TEXT
);

CREATE TABLE `developer` (
  developer_id TEXT,
  application_id TEXT
);

CREATE TABLE `domain` (
  domain_id INTEGER,
  domain_name TEXT
);

CREATE TABLE `domain_admin` (
  owner_id TEXT,
  domain_id TEXT
);

CREATE TABLE `event` (
  eid INTEGER,
  name TEXT,
  tagline TEXT,
  nid INTEGER,
  pic_small TEXT,
  pic_big TEXT,
  pic_square TEXT,
  pic TEXT,
  host TEXT,
  description TEXT,
  event_type TEXT,
  event_subtype TEXT,
  start_time INTEGER,
  end_time INTEGER,
  creator INTEGER,
  update_time INTEGER,
  location TEXT,
  venue ,
  privacy TEXT,
  hide_guest_list INTEGER,
  can_invite_friends INTEGER
);

CREATE TABLE `event_member` (
  uid TEXT,
  eid TEXT,
  rsvp_status TEXT,
  start_time INTEGER
);

CREATE TABLE `family` (
  profile_id TEXT,
  uid TEXT,
  name TEXT,
  birthday TEXT,
  relationship TEXT
);

CREATE TABLE `friend` (
  uid1 TEXT,
  uid2 TEXT
);

CREATE TABLE `friend_request` (
  uid_to TEXT,
  uid_from TEXT,
  time INTEGER,
  message TEXT,
  unread INTEGER
);

CREATE TABLE `friendlist` (
  owner INTEGER,
  flid TEXT,
  name TEXT
);

CREATE TABLE `friendlist_member` (
  flid TEXT,
  uid INTEGER
);

CREATE TABLE `group` (
  gid INTEGER,
  name TEXT,
  nid INTEGER,
  pic_small TEXT,
  pic_big TEXT,
  pic TEXT,
  description TEXT,
  group_type TEXT,
  group_subtype TEXT,
  recent_news TEXT,
  creator INTEGER,
  update_time INTEGER,
  office TEXT,
  website TEXT,
  venue ,
  privacy TEXT,
  icon TEXT,
  icon34 TEXT,
  icon68 TEXT,
  email TEXT,
  version INTEGER
);

CREATE TABLE `group_member` (
  uid TEXT,
  gid TEXT,
  administrator INTEGER,
  positions ,
  unread INTEGER,
  bookmark_order INTEGER
);

CREATE TABLE `like` (
  object_id INTEGER,
  post_id TEXT,
  user_id INTEGER,
  object_type TEXT
);

CREATE TABLE `link` (
  link_id INTEGER,
  owner INTEGER,
  owner_comment TEXT,
  created_time INTEGER,
  title TEXT,
  summary TEXT,
  url TEXT,
  picture TEXT,
  image_urls 
);

CREATE TABLE `link_stat` (
  url TEXT,
  normalized_url TEXT,
  share_count INTEGER,
  like_count INTEGER,
  comment_count INTEGER,
  total_count INTEGER,
  click_count INTEGER,
  comments_fbid INTEGER,
  commentsbox_count INTEGER
);

CREATE TABLE `mailbox_folder` (
  folder_id TEXT,
  viewer_id INTEGER,
  name TEXT,
  unread_count INTEGER,
  total_count INTEGER
);

CREATE TABLE `message` (
  message_id TEXT,
  thread_id TEXT,
  author_id INTEGER,
  body TEXT,
  created_time INTEGER,
  attachment ,
  viewer_id TEXT
);

CREATE TABLE `note` (
  uid INTEGER,
  note_id TEXT,
  created_time INTEGER,
  updated_time INTEGER,
  content TEXT,
  content_html TEXT,
  title TEXT
);

CREATE TABLE `notification` (
  notification_id TEXT,
  sender_id INTEGER,
  recipient_id INTEGER,
  created_time INTEGER,
  updated_time INTEGER,
  title_html TEXT,
  title_text TEXT,
  body_html TEXT,
  body_text TEXT,
  href TEXT,
  app_id INTEGER,
  is_unread INTEGER,
  is_hidden INTEGER,
  object_id TEXT,
  object_type TEXT,
  icon_url TEXT
);

CREATE TABLE `object_url` (
  url TEXT,
  id INTEGER,
  type TEXT,
  site TEXT
);

CREATE TABLE `page` (
  page_id INTEGER,
  name TEXT,
  username TEXT,
  description TEXT,
  categories ,
  is_community_page INTEGER,
  pic_small TEXT,
  pic_big TEXT,
  pic_square TEXT,
  pic TEXT,
  pic_large TEXT,
  page_url TEXT,
  fan_count INTEGER,
  type TEXT,
  website TEXT,
  has_added_app INTEGER,
  general_info TEXT,
  can_post INTEGER,
  checkins INTEGER,
  founded TEXT,
  company_overview TEXT,
  mission TEXT,
  products TEXT,
  location ,
  parking ,
  hours ,
  pharma_safety_info TEXT,
  public_transit TEXT,
  attire TEXT,
  payment_options ,
  culinary_team TEXT,
  general_manager TEXT,
  price_range TEXT,
  restaurant_services ,
  restaurant_specialties ,
  phone TEXT,
  release_date TEXT,
  genre TEXT,
  starring TEXT,
  screenplay_by TEXT,
  directed_by TEXT,
  produced_by TEXT,
  studio TEXT,
  awards TEXT,
  plot_outline TEXT,
  season TEXT,
  network TEXT,
  schedule TEXT,
  written_by TEXT,
  band_members TEXT,
  hometown TEXT,
  current_location TEXT,
  record_label TEXT,
  booking_agent TEXT,
  press_contact TEXT,
  artists_we_like TEXT,
  influences TEXT,
  band_interests TEXT,
  bio TEXT,
  affiliation TEXT,
  birthday TEXT,
  personal_info TEXT,
  personal_interests TEXT,
  built TEXT,
  features TEXT,
  mpg TEXT
);

CREATE TABLE `page_admin` (
  uid TEXT,
  page_id TEXT,
  type TEXT
);

CREATE TABLE `page_blocked_user` (
  page_id TEXT,
  uid TEXT
);

CREATE TABLE `page_fan` (
  uid INTEGER,
  page_id INTEGER,
  type TEXT,
  profile_section TEXT,
  created_time INTEGER
);

CREATE TABLE `permissions_info` (
  permission_name TEXT,
  header TEXT,
  summary TEXT
);

CREATE TABLE `photo` (
  pid TEXT,
  aid TEXT,
  owner TEXT,
  src_small TEXT,
  src_small_width INTEGER,
  src_small_height INTEGER,
  src_big TEXT,
  src_big_width INTEGER,
  src_big_height INTEGER,
  src TEXT,
  src_width INTEGER,
  src_height INTEGER,
  link TEXT,
  caption TEXT,
  created INTEGER,
  modified INTEGER,
  position INTEGER,
  object_id INTEGER,
  album_object_id INTEGER,
  images 
);

CREATE TABLE `photo_tag` (
  pid TEXT,
  subject TEXT,
  object_id INTEGER,
  text TEXT,
  xcoord REAL,
  ycoord REAL,
  created INTEGER
);

CREATE TABLE `place` (
  page_id INTEGER,
  name TEXT,
  description TEXT,
  geometry ,
  latitude INTEGER,
  longitude INTEGER,
  checkin_count INTEGER,
  display_subtext TEXT
);

CREATE TABLE `privacy` (
  id INTEGER,
  object_id INTEGER,
  value TEXT,
  description TEXT,
  allow TEXT,
  deny TEXT,
  owner_id INTEGER,
  networks INTEGER,
  friends TEXT
);

CREATE TABLE `privacy_setting` (
  name TEXT,
  value TEXT,
  description TEXT,
  allow TEXT,
  deny TEXT,
  networks INTEGER,
  friends TEXT
);

CREATE TABLE `profile` (
  id INTEGER,
  can_post INTEGER,
  name TEXT,
  url TEXT,
  pic TEXT,
  pic_square TEXT,
  pic_small TEXT,
  pic_big TEXT,
  pic_crop ,
  type TEXT,
  username TEXT
);

CREATE TABLE `question` (
  id INTEGER,
  owner INTEGER,
  question TEXT,
  created_time INTEGER,
  updated_time INTEGER
);

CREATE TABLE `question_option` (
  id INTEGER,
  question_id TEXT,
  name TEXT,
  votes INTEGER,
  object_id INTEGER,
  owner INTEGER,
  created_time INTEGER
);

CREATE TABLE `question_option_votes` (
  option_id INTEGER,
  voter_id INTEGER
);

CREATE TABLE `review` (
  reviewee_id INTEGER,
  reviewer_id INTEGER,
  review_id INTEGER,
  message TEXT,
  created_time INTEGER,
  rating INTEGER
);

CREATE TABLE `standard_friend_info` (
  uid1 INTEGER,
  uid2 INTEGER
);

CREATE TABLE `standard_user_info` (
  uid TEXT,
  name TEXT,
  username TEXT,
  third_party_id TEXT,
  first_name TEXT,
  last_name TEXT,
  locale TEXT,
  affiliations ,
  profile_url TEXT,
  timezone TEXT,
  birthday TEXT,
  sex TEXT,
  proxied_email TEXT,
  current_location TEXT,
  allowed_restrictions TEXT
);

CREATE TABLE `status` (
  uid INTEGER,
  status_id INTEGER,
  time INTEGER,
  source INTEGER,
  message TEXT
);

CREATE TABLE `stream` (
  post_id TEXT,
  viewer_id INTEGER,
  app_id INTEGER,
  source_id INTEGER,
  updated_time INTEGER,
  created_time INTEGER,
  filter_key TEXT,
  attribution TEXT,
  actor_id INTEGER,
  target_id TEXT,
  message TEXT,
  app_data ,
  action_links ,
  attachment ,
  impressions INTEGER,
  comments ,
  likes ,
  privacy ,
  permalink TEXT,
  xid INTEGER,
  tagged_ids ,
  message_tags ,
  description TEXT,
  description_tags 
);

CREATE TABLE `stream_filter` (
  uid INTEGER,
  filter_key TEXT,
  name TEXT,
  rank INTEGER,
  icon_url TEXT,
  is_visible INTEGER,
  type TEXT,
  value INTEGER
);

CREATE TABLE `stream_tag` (
  post_id TEXT,
  actor_id TEXT,
  target_id TEXT
);

CREATE TABLE `thread` (
  thread_id TEXT,
  folder_id TEXT,
  subject TEXT,
  recipients ,
  updated_time INTEGER,
  parent_message_id TEXT,
  parent_thread_id INTEGER,
  message_count INTEGER,
  snippet TEXT,
  snippet_author INTEGER,
  object_id INTEGER,
  unread INTEGER,
  viewer_id TEXT
);

CREATE TABLE `translation` (
  locale TEXT,
  native_hash TEXT,
  native_string TEXT,
  description TEXT,
  translation TEXT,
  approval_status TEXT,
  pre_hash_string TEXT,
  best_string TEXT
);

CREATE TABLE `unified_message` (
  message_id TEXT,
  thread_id TEXT,
  subject TEXT,
  body TEXT,
  unread INTEGER,
  action_id TEXT,
  timestamp TEXT,
  tags ,
  sender ,
  recipients ,
  object_sender ,
  html_body TEXT,
  attachments ,
  attachment_map ,
  shares ,
  share_map 
);

CREATE TABLE `unified_thread` (
  action_id TEXT,
  archived INTEGER,
  can_reply INTEGER,
  folder TEXT,
  former_participants ,
  has_attachments INTEGER,
  is_subscribed INTEGER,
  last_visible_add_action_id TEXT,
  name TEXT,
  num_messages INTEGER,
  num_unread INTEGER,
  object_participants ,
  participants ,
  senders ,
  single_recipient TEXT,
  snippet TEXT,
  snippet_sender ,
  snippet_message_has_attachment INTEGER,
  subject TEXT,
  tags ,
  thread_id TEXT,
  thread_participants ,
  timestamp TEXT,
  unread INTEGER
);

CREATE TABLE `unified_thread_action` (
  action_id TEXT,
  actor ,
  thread_id TEXT,
  timestamp TEXT,
  type INTEGER,
  users 
);

CREATE TABLE `unified_thread_count` (
  folder TEXT,
  unread_count INTEGER,
  unseen_count INTEGER,
  last_action_id INTEGER,
  last_seen_time INTEGER,
  total_threads INTEGER
);

CREATE TABLE `url_like` (
  user_id TEXT,
  url TEXT
);

CREATE TABLE `user` (
  uid INTEGER,
  username TEXT,
  first_name TEXT,
  middle_name TEXT,
  last_name TEXT,
  name TEXT,
  pic_small TEXT,
  pic_big TEXT,
  pic_square TEXT,
  pic TEXT,
  affiliations ,
  profile_update_time INTEGER,
  timezone INTEGER,
  religion TEXT,
  birthday TEXT,
  birthday_date TEXT,
  sex TEXT,
  hometown_location ,
  meeting_sex ,
  meeting_for ,
  relationship_status TEXT,
  significant_other_id INTEGER,
  political TEXT,
  current_location ,
  activities TEXT,
  interests TEXT,
  is_app_user INTEGER,
  music TEXT,
  tv TEXT,
  movies TEXT,
  books TEXT,
  quotes TEXT,
  about_me TEXT,
  hs_info ,
  education_history ,
  work_history ,
  notes_count INTEGER,
  wall_count INTEGER,
  status TEXT,
  has_added_app INTEGER,
  online_presence TEXT,
  locale TEXT,
  proxied_email TEXT,
  profile_url TEXT,
  email_hashes ,
  pic_small_with_logo TEXT,
  pic_big_with_logo TEXT,
  pic_square_with_logo TEXT,
  pic_with_logo TEXT,
  allowed_restrictions TEXT,
  verified INTEGER,
  profile_blurb TEXT,
  family ,
  website TEXT,
  is_blocked INTEGER,
  contact_email TEXT,
  email TEXT,
  third_party_id TEXT,
  name_format TEXT,
  video_upload_limits ,
  games TEXT,
  is_minor INTEGER,
  work ,
  education ,
  sports ,
  favorite_athletes ,
  favorite_teams ,
  inspirational_people ,
  languages ,
  likes_count INTEGER,
  friend_count INTEGER,
  mutual_friend_count INTEGER,
  can_post INTEGER
);

CREATE TABLE `video` (
  vid INTEGER,
  owner INTEGER,
  album_id INTEGER,
  title TEXT,
  description TEXT,
  link TEXT,
  thumbnail_link TEXT,
  embed_html TEXT,
  updated_time INTEGER,
  created_time INTEGER,
  length REAL,
  src TEXT,
  src_hq TEXT
);

CREATE TABLE `video_tag` (
  vid TEXT,
  subject INTEGER,
  updated_time INTEGER,
  created_time INTEGER
);

