-- Do not edit! Generated automatically by mockfacebook.
-- https://github.com/rogerhu/mockfacebook
-- 2012-10-23 22:34:02.059169


CREATE TABLE IF NOT EXISTS `album` (
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
  video_count INTEGER,
  like_info ,
  comment_info ,
  UNIQUE (aid, object_id, owner, cover_pid, cover_object_id, name, created, modified, description, location, size, link, visible, modified_major, edit_link, type, can_upload, photo_count, video_count, like_info, comment_info)
);

CREATE TABLE IF NOT EXISTS `application` (
  app_id TEXT,
  api_key TEXT,
  namespace TEXT,
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
  restriction_info ,
  app_domains ,
  auth_dialog_data_help_url TEXT,
  auth_dialog_description TEXT,
  auth_dialog_headline TEXT,
  auth_dialog_perms_explanation TEXT,
  auth_referral_user_perms ,
  auth_referral_friend_perms ,
  auth_referral_default_activity_privacy TEXT,
  auth_referral_enabled INTEGER,
  auth_referral_extended_perms ,
  auth_referral_response_type TEXT,
  canvas_fluid_height INTEGER,
  canvas_fluid_width INTEGER,
  canvas_url TEXT,
  contact_email TEXT,
  created_time INTEGER,
  creator_uid INTEGER,
  deauth_callback_url TEXT,
  iphone_app_store_id TEXT,
  hosting_url TEXT,
  mobile_web_url TEXT,
  page_tab_default_name TEXT,
  page_tab_url TEXT,
  privacy_policy_url TEXT,
  secure_canvas_url TEXT,
  secure_page_tab_url TEXT,
  server_ip_whitelist TEXT,
  social_discovery INTEGER,
  terms_of_service_url TEXT,
  update_ip_whitelist TEXT,
  user_support_email TEXT,
  user_support_url TEXT,
  website_url TEXT,
  UNIQUE (app_id, api_key, namespace, display_name, icon_url, logo_url, company_name, developers, description, daily_active_users, weekly_active_users, monthly_active_users, category, subcategory, is_facebook_app, restriction_info, app_domains, auth_dialog_data_help_url, auth_dialog_description, auth_dialog_headline, auth_dialog_perms_explanation, auth_referral_user_perms, auth_referral_friend_perms, auth_referral_default_activity_privacy, auth_referral_enabled, auth_referral_extended_perms, auth_referral_response_type, canvas_fluid_height, canvas_fluid_width, canvas_url, contact_email, created_time, creator_uid, deauth_callback_url, iphone_app_store_id, hosting_url, mobile_web_url, page_tab_default_name, page_tab_url, privacy_policy_url, secure_canvas_url, secure_page_tab_url, server_ip_whitelist, social_discovery, terms_of_service_url, update_ip_whitelist, user_support_email, user_support_url, website_url)
);

CREATE TABLE IF NOT EXISTS `apprequest` (
  request_id TEXT,
  app_id TEXT,
  recipient_uid TEXT,
  sender_uid TEXT,
  message TEXT,
  data TEXT,
  created_time INTEGER,
  UNIQUE (request_id, app_id, recipient_uid, sender_uid, message, data, created_time)
);

CREATE TABLE IF NOT EXISTS `checkin` (
  checkin_id INTEGER,
  author_uid INTEGER,
  page_id INTEGER,
  app_id INTEGER,
  post_id INTEGER,
  coords ,
  timestamp INTEGER,
  tagged_uids ,
  message TEXT,
  UNIQUE (checkin_id, author_uid, page_id, app_id, post_id, coords, timestamp, tagged_uids, message)
);

CREATE TABLE IF NOT EXISTS `comment` (
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
  can_like INTEGER,
  user_likes INTEGER,
  text_tags ,
  is_private INTEGER,
  UNIQUE (xid, object_id, post_id, fromid, time, text, id, username, reply_xid, post_fbid, app_id, likes, comments, can_like, user_likes, text_tags, is_private)
);

CREATE TABLE IF NOT EXISTS `comments_info` (
  app_id TEXT,
  xid TEXT,
  count INTEGER,
  updated_time INTEGER,
  UNIQUE (app_id, xid, count, updated_time)
);

CREATE TABLE IF NOT EXISTS `connection` (
  source_id INTEGER,
  target_id INTEGER,
  target_type TEXT,
  is_following INTEGER,
  UNIQUE (source_id, target_id, target_type, is_following)
);

CREATE TABLE IF NOT EXISTS `cookies` (
  uid TEXT,
  name TEXT,
  value TEXT,
  expires INTEGER,
  path TEXT,
  UNIQUE (uid, name, value, expires, path)
);

CREATE TABLE IF NOT EXISTS `developer` (
  developer_id TEXT,
  application_id TEXT,
  role TEXT,
  UNIQUE (developer_id, application_id, role)
);

CREATE TABLE IF NOT EXISTS `domain` (
  domain_id INTEGER,
  domain_name TEXT,
  UNIQUE (domain_id, domain_name)
);

CREATE TABLE IF NOT EXISTS `domain_admin` (
  owner_id TEXT,
  domain_id TEXT,
  UNIQUE (owner_id, domain_id)
);

CREATE TABLE IF NOT EXISTS `event` (
  eid INTEGER,
  name TEXT,
  pic_small TEXT,
  pic_big TEXT,
  pic_square TEXT,
  pic TEXT,
  host TEXT,
  description TEXT,
  start_time TEXT,
  end_time TEXT,
  creator INTEGER,
  update_time INTEGER,
  location TEXT,
  venue ,
  privacy TEXT,
  hide_guest_list INTEGER,
  can_invite_friends INTEGER,
  all_members_count INTEGER,
  attending_count INTEGER,
  unsure_count INTEGER,
  declined_count INTEGER,
  not_replied_count INTEGER,
  UNIQUE (eid, name, pic_small, pic_big, pic_square, pic, host, description, start_time, end_time, creator, update_time, location, venue, privacy, hide_guest_list, can_invite_friends, all_members_count, attending_count, unsure_count, declined_count, not_replied_count)
);

CREATE TABLE IF NOT EXISTS `event_member` (
  uid TEXT,
  eid TEXT,
  rsvp_status TEXT,
  start_time TEXT,
  UNIQUE (uid, eid, rsvp_status, start_time)
);

CREATE TABLE IF NOT EXISTS `family` (
  profile_id TEXT,
  uid TEXT,
  name TEXT,
  birthday TEXT,
  relationship TEXT,
  UNIQUE (profile_id, uid, name, birthday, relationship)
);

CREATE TABLE IF NOT EXISTS `friend` (
  uid1 TEXT,
  uid2 TEXT,
  UNIQUE (uid1, uid2)
);

CREATE TABLE IF NOT EXISTS `friend_request` (
  uid_to TEXT,
  uid_from TEXT,
  time INTEGER,
  message TEXT,
  unread INTEGER,
  UNIQUE (uid_to, uid_from, time, message, unread)
);

CREATE TABLE IF NOT EXISTS `friendlist` (
  owner INTEGER,
  flid TEXT,
  name TEXT,
  type TEXT,
  UNIQUE (owner, flid, name, type)
);

CREATE TABLE IF NOT EXISTS `friendlist_member` (
  flid TEXT,
  uid INTEGER,
  UNIQUE (flid, uid)
);

CREATE TABLE IF NOT EXISTS `group` (
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
  version INTEGER,
  UNIQUE (gid, name, nid, pic_small, pic_big, pic, description, group_type, group_subtype, recent_news, creator, update_time, office, website, venue, privacy, icon, icon34, icon68, email, version)
);

CREATE TABLE IF NOT EXISTS `group_member` (
  uid TEXT,
  gid TEXT,
  administrator INTEGER,
  positions ,
  unread INTEGER,
  bookmark_order INTEGER,
  UNIQUE (uid, gid, administrator, positions, unread, bookmark_order)
);

CREATE TABLE IF NOT EXISTS `like` (
  object_id INTEGER,
  post_id TEXT,
  user_id INTEGER,
  object_type TEXT,
  UNIQUE (object_id, post_id, user_id, object_type)
);

CREATE TABLE IF NOT EXISTS `link` (
  link_id INTEGER,
  owner INTEGER,
  owner_comment TEXT,
  created_time INTEGER,
  title TEXT,
  summary TEXT,
  url TEXT,
  picture TEXT,
  image_urls ,
  UNIQUE (link_id, owner, owner_comment, created_time, title, summary, url, picture, image_urls)
);

CREATE TABLE IF NOT EXISTS `link_stat` (
  url TEXT,
  normalized_url TEXT,
  share_count INTEGER,
  like_count INTEGER,
  comment_count INTEGER,
  total_count INTEGER,
  click_count INTEGER,
  comments_fbid INTEGER,
  commentsbox_count INTEGER,
  UNIQUE (url, normalized_url, share_count, like_count, comment_count, total_count, click_count, comments_fbid, commentsbox_count)
);

CREATE TABLE IF NOT EXISTS `location_post` (
  id INTEGER,
  author_uid INTEGER,
  app_id INTEGER,
  timestamp INTEGER,
  tagged_uids ,
  page_id INTEGER,
  page_type TEXT,
  coords ,
  type TEXT,
  UNIQUE (id, author_uid, app_id, timestamp, tagged_uids, page_id, page_type, coords, type)
);

CREATE TABLE IF NOT EXISTS `mailbox_folder` (
  folder_id TEXT,
  viewer_id TEXT,
  name TEXT,
  unread_count INTEGER,
  total_count INTEGER,
  UNIQUE (folder_id, viewer_id, name, unread_count, total_count)
);

CREATE TABLE IF NOT EXISTS `message` (
  message_id TEXT,
  thread_id TEXT,
  author_id INTEGER,
  body TEXT,
  created_time INTEGER,
  attachment ,
  viewer_id TEXT,
  UNIQUE (message_id, thread_id, author_id, body, created_time, attachment, viewer_id)
);

CREATE TABLE IF NOT EXISTS `note` (
  uid INTEGER,
  note_id TEXT,
  created_time INTEGER,
  updated_time INTEGER,
  content TEXT,
  content_html TEXT,
  title TEXT,
  like_info ,
  comment_info ,
  UNIQUE (uid, note_id, created_time, updated_time, content, content_html, title, like_info, comment_info)
);

CREATE TABLE IF NOT EXISTS `notification` (
  notification_id TEXT,
  sender_id INTEGER,
  recipient_id INTEGER,
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
  icon_url TEXT,
  UNIQUE (notification_id, sender_id, recipient_id, title_html, title_text, body_html, body_text, href, app_id, is_unread, is_hidden, object_id, object_type, icon_url)
);

CREATE TABLE IF NOT EXISTS `object_url` (
  url TEXT,
  id INTEGER,
  type TEXT,
  site TEXT,
  UNIQUE (url, id, type, site)
);

CREATE TABLE IF NOT EXISTS `offer` (
  id INTEGER,
  owner_id INTEGER,
  title TEXT,
  image_url TEXT,
  terms TEXT,
  claim_limit INTEGER,
  created_time INTEGER,
  expiration_time TEXT,
  UNIQUE (id, owner_id, title, image_url, terms, claim_limit, created_time, expiration_time)
);

CREATE TABLE IF NOT EXISTS `page` (
  page_id INTEGER,
  name TEXT,
  username TEXT,
  description TEXT,
  page_url TEXT,
  categories ,
  is_community_page INTEGER,
  pic_small TEXT,
  pic_big TEXT,
  pic_square TEXT,
  pic TEXT,
  pic_large TEXT,
  pic_cover ,
  unread_notif_count INTEGER,
  new_like_count INTEGER,
  fan_count INTEGER,
  global_brand_like_count INTEGER,
  global_brand_talking_about_count INTEGER,
  global_brand_parent_page_id INTEGER,
  type TEXT,
  website TEXT,
  has_added_app INTEGER,
  general_info TEXT,
  can_post INTEGER,
  checkins INTEGER,
  is_published INTEGER,
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
  mpg TEXT,
  UNIQUE (page_id, name, username, description, page_url, categories, is_community_page, pic_small, pic_big, pic_square, pic, pic_large, pic_cover, unread_notif_count, new_like_count, fan_count, global_brand_like_count, global_brand_talking_about_count, global_brand_parent_page_id, type, website, has_added_app, general_info, can_post, checkins, is_published, founded, company_overview, mission, products, location, parking, hours, pharma_safety_info, public_transit, attire, payment_options, culinary_team, general_manager, price_range, restaurant_services, restaurant_specialties, phone, release_date, genre, starring, screenplay_by, directed_by, produced_by, studio, awards, plot_outline, season, network, schedule, written_by, band_members, hometown, current_location, record_label, booking_agent, press_contact, artists_we_like, influences, band_interests, bio, affiliation, birthday, personal_info, personal_interests, built, features, mpg)
);

CREATE TABLE IF NOT EXISTS `page_admin` (
  uid TEXT,
  page_id TEXT,
  type TEXT,
  UNIQUE (uid, page_id, type)
);

CREATE TABLE IF NOT EXISTS `page_blocked_user` (
  page_id TEXT,
  uid TEXT,
  UNIQUE (page_id, uid)
);

CREATE TABLE IF NOT EXISTS `page_fan` (
  uid INTEGER,
  page_id INTEGER,
  type TEXT,
  profile_section TEXT,
  created_time INTEGER,
  UNIQUE (uid, page_id, type, profile_section, created_time)
);

CREATE TABLE IF NOT EXISTS `page_global_brand_child` (
  parent_page_id INTEGER,
  global_brand_child_page_id INTEGER,
  UNIQUE (parent_page_id, global_brand_child_page_id)
);

CREATE TABLE IF NOT EXISTS `page_milestone` (
  id INTEGER,
  owner_id INTEGER,
  title TEXT,
  description TEXT,
  created_time INTEGER,
  updated_time INTEGER,
  start_time INTEGER,
  end_time INTEGER,
  UNIQUE (id, owner_id, title, description, created_time, updated_time, start_time, end_time)
);

CREATE TABLE IF NOT EXISTS `permissions_info` (
  permission_name TEXT,
  header TEXT,
  summary TEXT,
  UNIQUE (permission_name, header, summary)
);

CREATE TABLE IF NOT EXISTS `photo` (
  object_id INTEGER,
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
  caption_tags ,
  created INTEGER,
  modified INTEGER,
  position INTEGER,
  album_object_id INTEGER,
  place_id INTEGER,
  images ,
  like_info ,
  comment_info ,
  can_delete INTEGER,
  UNIQUE (object_id, pid, aid, owner, src_small, src_small_width, src_small_height, src_big, src_big_width, src_big_height, src, src_width, src_height, link, caption, caption_tags, created, modified, position, album_object_id, place_id, images, like_info, comment_info, can_delete)
);

CREATE TABLE IF NOT EXISTS `photo_src` (
  photo_id INTEGER,
  size TEXT,
  width INTEGER,
  height INTEGER,
  src TEXT,
  UNIQUE (photo_id, size, width, height, src)
);

CREATE TABLE IF NOT EXISTS `photo_tag` (
  object_id INTEGER,
  pid TEXT,
  subject TEXT,
  text TEXT,
  xcoord REAL,
  ycoord REAL,
  created INTEGER,
  UNIQUE (object_id, pid, subject, text, xcoord, ycoord, created)
);

CREATE TABLE IF NOT EXISTS `place` (
  page_id INTEGER,
  name TEXT,
  description TEXT,
  geometry ,
  latitude REAL,
  longitude REAL,
  checkin_count INTEGER,
  display_subtext TEXT,
  UNIQUE (page_id, name, description, geometry, latitude, longitude, checkin_count, display_subtext)
);

CREATE TABLE IF NOT EXISTS `privacy` (
  id INTEGER,
  object_id INTEGER,
  value TEXT,
  description TEXT,
  allow TEXT,
  deny TEXT,
  owner_id INTEGER,
  networks INTEGER,
  friends TEXT,
  UNIQUE (id, object_id, value, description, allow, deny, owner_id, networks, friends)
);

CREATE TABLE IF NOT EXISTS `privacy_setting` (
  name TEXT,
  value TEXT,
  description TEXT,
  allow TEXT,
  deny TEXT,
  networks INTEGER,
  friends TEXT,
  UNIQUE (name, value, description, allow, deny, networks, friends)
);

CREATE TABLE IF NOT EXISTS `profile` (
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
  username TEXT,
  UNIQUE (id, can_post, name, url, pic, pic_square, pic_small, pic_big, pic_crop, type, username)
);

CREATE TABLE IF NOT EXISTS `profile_pic` (
  id INTEGER,
  width INTEGER,
  height INTEGER,
  url TEXT,
  is_silhouette INTEGER,
  real_width INTEGER,
  real_height INTEGER,
  UNIQUE (id, width, height, url, is_silhouette, real_width, real_height)
);

CREATE TABLE IF NOT EXISTS `profile_view` (
  profile_id INTEGER,
  app_id INTEGER,
  link TEXT,
  custom_image_url TEXT,
  position INTEGER,
  is_permanent INTEGER,
  UNIQUE (profile_id, app_id, link, custom_image_url, position, is_permanent)
);

CREATE TABLE IF NOT EXISTS `question` (
  id INTEGER,
  owner INTEGER,
  question TEXT,
  created_time INTEGER,
  updated_time INTEGER,
  UNIQUE (id, owner, question, created_time, updated_time)
);

CREATE TABLE IF NOT EXISTS `question_option` (
  id INTEGER,
  question_id TEXT,
  name TEXT,
  votes INTEGER,
  object_id INTEGER,
  owner INTEGER,
  created_time INTEGER,
  UNIQUE (id, question_id, name, votes, object_id, owner, created_time)
);

CREATE TABLE IF NOT EXISTS `question_option_votes` (
  option_id INTEGER,
  voter_id INTEGER,
  UNIQUE (option_id, voter_id)
);

CREATE TABLE IF NOT EXISTS `review` (
  reviewee_id INTEGER,
  reviewer_id INTEGER,
  review_id INTEGER,
  message TEXT,
  created_time INTEGER,
  rating INTEGER,
  UNIQUE (reviewee_id, reviewer_id, review_id, message, created_time, rating)
);

CREATE TABLE IF NOT EXISTS `standard_friend_info` (
  uid1 INTEGER,
  uid2 INTEGER,
  UNIQUE (uid1, uid2)
);

CREATE TABLE IF NOT EXISTS `standard_user_info` (
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
  allowed_restrictions TEXT,
  UNIQUE (uid, name, username, third_party_id, first_name, last_name, locale, affiliations, profile_url, timezone, birthday, sex, proxied_email, current_location, allowed_restrictions)
);

CREATE TABLE IF NOT EXISTS `status` (
  uid INTEGER,
  status_id INTEGER,
  time INTEGER,
  source INTEGER,
  message TEXT,
  place_id INTEGER,
  UNIQUE (uid, status_id, time, source, message, place_id)
);

CREATE TABLE IF NOT EXISTS `stream` (
  post_id TEXT,
  viewer_id INTEGER,
  app_id INTEGER,
  source_id INTEGER,
  updated_time INTEGER,
  created_time INTEGER,
  filter_key TEXT,
  attribution TEXT,
  actor_id INTEGER,
  target_id INTEGER,
  message TEXT,
  app_data ,
  action_links ,
  attachment ,
  impressions INTEGER,
  comments ,
  likes ,
  place INTEGER,
  privacy ,
  permalink TEXT,
  xid INTEGER,
  tagged_ids ,
  message_tags ,
  description TEXT,
  description_tags ,
  type INTEGER,
  UNIQUE (post_id, viewer_id, app_id, source_id, updated_time, created_time, filter_key, attribution, actor_id, target_id, message, app_data, action_links, attachment, impressions, comments, likes, place, privacy, permalink, xid, tagged_ids, message_tags, description, description_tags, type)
);

CREATE TABLE IF NOT EXISTS `stream_filter` (
  uid INTEGER,
  filter_key TEXT,
  name TEXT,
  rank INTEGER,
  icon_url TEXT,
  is_visible INTEGER,
  type TEXT,
  value INTEGER,
  UNIQUE (uid, filter_key, name, rank, icon_url, is_visible, type, value)
);

CREATE TABLE IF NOT EXISTS `stream_tag` (
  post_id TEXT,
  actor_id TEXT,
  target_id TEXT,
  UNIQUE (post_id, actor_id, target_id)
);

CREATE TABLE IF NOT EXISTS `thread` (
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
  viewer_id TEXT,
  UNIQUE (thread_id, folder_id, subject, recipients, updated_time, parent_message_id, parent_thread_id, message_count, snippet, snippet_author, object_id, unread, viewer_id)
);

CREATE TABLE IF NOT EXISTS `translation` (
  locale TEXT,
  native_hash TEXT,
  native_string TEXT,
  description TEXT,
  translation TEXT,
  approval_status TEXT,
  pre_hash_string TEXT,
  best_string TEXT,
  UNIQUE (locale, native_hash, native_string, description, translation, approval_status, pre_hash_string, best_string)
);

CREATE TABLE IF NOT EXISTS `unified_message` (
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
  share_map ,
  UNIQUE (message_id, thread_id, subject, body, unread, action_id, timestamp, tags, sender, recipients, object_sender, html_body, attachments, attachment_map, shares, share_map)
);

CREATE TABLE IF NOT EXISTS `unified_thread` (
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
  unread INTEGER,
  UNIQUE (action_id, archived, can_reply, folder, former_participants, has_attachments, is_subscribed, last_visible_add_action_id, name, num_messages, num_unread, object_participants, participants, senders, single_recipient, snippet, snippet_sender, snippet_message_has_attachment, subject, tags, thread_id, thread_participants, timestamp, unread)
);

CREATE TABLE IF NOT EXISTS `unified_thread_action` (
  action_id TEXT,
  actor ,
  thread_id TEXT,
  timestamp TEXT,
  type INTEGER,
  users ,
  UNIQUE (action_id, actor, thread_id, timestamp, type, users)
);

CREATE TABLE IF NOT EXISTS `unified_thread_count` (
  folder TEXT,
  unread_count INTEGER,
  unseen_count INTEGER,
  last_action_id INTEGER,
  last_seen_time INTEGER,
  total_threads INTEGER,
  UNIQUE (folder, unread_count, unseen_count, last_action_id, last_seen_time, total_threads)
);

CREATE TABLE IF NOT EXISTS `url_like` (
  user_id TEXT,
  url TEXT,
  UNIQUE (user_id, url)
);

CREATE TABLE IF NOT EXISTS `user` (
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
  devices ,
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
  pic_cover ,
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
  can_post INTEGER,
  UNIQUE (uid, username, first_name, middle_name, last_name, name, pic_small, pic_big, pic_square, pic, affiliations, profile_update_time, timezone, religion, birthday, birthday_date, devices, sex, hometown_location, meeting_sex, meeting_for, relationship_status, significant_other_id, political, current_location, activities, interests, is_app_user, music, tv, movies, books, quotes, about_me, hs_info, education_history, work_history, notes_count, wall_count, status, has_added_app, online_presence, locale, proxied_email, profile_url, email_hashes, pic_small_with_logo, pic_big_with_logo, pic_square_with_logo, pic_with_logo, pic_cover, allowed_restrictions, verified, profile_blurb, family, website, is_blocked, contact_email, email, third_party_id, name_format, video_upload_limits, games, work, education, sports, favorite_athletes, favorite_teams, inspirational_people, languages, likes_count, friend_count, mutual_friend_count, can_post)
);

CREATE TABLE IF NOT EXISTS `video` (
  vid INTEGER,
  owner INTEGER,
  title TEXT,
  description TEXT,
  link TEXT,
  thumbnail_link TEXT,
  embed_html TEXT,
  updated_time INTEGER,
  created_time INTEGER,
  length REAL,
  src TEXT,
  src_hq TEXT,
  UNIQUE (vid, owner, title, description, link, thumbnail_link, embed_html, updated_time, created_time, length, src, src_hq)
);

CREATE TABLE IF NOT EXISTS `video_tag` (
  vid TEXT,
  subject INTEGER,
  updated_time INTEGER,
  created_time INTEGER,
  UNIQUE (vid, subject, updated_time, created_time)
);

