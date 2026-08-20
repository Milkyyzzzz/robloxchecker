import re
import requests
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Roblox Advanced ID & User Search", page_icon="🔍", layout="centered"
)

st.title("🔍 Roblox Advanced User & ID Scanner")
st.write(
    "Search for users by username keyword, exact User ID, or scan users "
    "**near a specific User ID**, then check them against your bulk list of "
    "Groups, Friends, or Badges!"
)

# 1. Selection for Lookup Method
lookup_method = st.radio(
    "Choose How to Find the Target User(s):",
    [
        "Search Username (Keyword)",
        "Enter Exact User ID & Scan Near IDs",
    ],
)

selected_user_id = None
user_id_list = []

if lookup_method == "Search Username (Keyword)":
  keyword = st.text_input(
      "Enter Username Keyword",
      "Builder",
      help="Type a username or part of a name to search like on Roblox.",
  )
  if keyword.strip():
    try:
      search_url = f"https://users.roblox.com/v1/users/search?keyword={keyword}&limit=10"
      res = requests.get(search_url)
      if res.status_code == 200:
        search_data = res.json().get("data", [])
        if search_data:
          user_options = {
              f"{u['displayName']} (@{u['name']} - ID: {u['id']})": u["id"]
              for u in search_data
          }
          chosen_label = st.selectbox(
              "Select a User from Search Results:", list(user_options.keys())
          )
          selected_user_id = user_options[chosen_label]
        else:
          st.info("No users found matching that keyword.")
      else:
        st.error("Error communicating with Roblox search API.")
    except Exception as e:
      st.error(f"Search failed: {e}")

else:
  col1, col2 = st.columns([2, 1])
  with col1:
    base_user_id = st.number_input(
        "Roblox User ID", min_value=1, value=1, step=1
    )
  with col2:
    scan_range = st.slider(
        "Scan Near IDs (+/- range)",
        min_value=0,
        max_value=10,
        value=0,
        help=(
            "Scans user IDs numerically close to the target ID (useful for"
            " finding accounts created around the same time)."
        ),
    )

  for offset in range(-scan_range, scan_range + 1):
    uid = base_user_id + offset
    if uid > 0:
      user_id_list.append(uid)

  if len(user_id_list) == 1:
    selected_user_id = user_id_list[0]

# Selection for what to check against
st.divider()
check_type = st.selectbox(
    "Select What to Check:",
    ["Groups Membership", "Friends List", "Badge Ownership"],
)

raw_ids_input = st.text_area(
    "Paste Raw IDs to Verify (Groups, Friends, or Badges)",
    placeholder="123456, 7891011\n121314",
    help="Paste your bulk list of target IDs separated by commas, spaces, or newlines.",
)


def parse_ids(raw_text):
  if not raw_text:
    return []
  id_strings = re.findall(r"\d+", raw_text)
  return [int(i) for i in id_strings]


if st.button("Run Multi-Check", type="primary"):
  target_ids = parse_ids(raw_ids_input)

  if not target_ids:
    st.warning("Please enter or paste at least one target ID to verify against.")
  else:
    # Determine users to evaluate
    users_to_check = []
    if lookup_method == "Search Username (Keyword)" and selected_user_id:
      users_to_check = [selected_user_id]
    elif lookup_method == "Enter Exact User ID & Scan Near IDs":
      users_to_check = user_id_list

    if not users_to_check:
      st.warning("No valid user selected or found.")
    else:
      for uid in users_to_check:
        with st.spinner(f"Analyzing User ID {uid}..."):
          # Fetch user details
          user_url = f"https://users.roblox.com/v1/users/{uid}"
          u_resp = requests.get(user_url)
          if u_resp.status_code != 200:
            st.info(f"User ID `{uid}` does not exist or is banned/deleted.")
            continue

          u_data = u_resp.json()
          username = u_data.get("name", "Unknown")
          display_name = u_data.get("displayName", "Unknown")
          is_banned = u_data.get("isBanned", False)

          if is_banned:
            st.warning(f"User ID `{uid}` is banned/terminated.")
            continue

          st.markdown(
              f"### 👤 User: {display_name} (`@{username}` | ID: `{uid}`)"
          )

          # --- CHECK GROUPS ---
          if check_type == "Groups Membership":
            groups_url = (
                f"https://groups.roblox.com/v2/users/{uid}/groups/roles"
            )
            g_resp = requests.get(groups_url)
            g_data = g_resp.json() if g_resp.status_code == 200 else {}

            user_groups = {}
            for item in g_data.get("data", []):
              g_id = item["group"]["id"]
              g_name = item["group"]["name"]
              r_name = item["role"]["name"]
              user_groups[g_id] = {"group_name": g_name, "role": r_name}

            matches = 0
            for tid in target_ids:
              if tid in user_groups:
                matches += 1
                st.success(
                    f"✅ **Group ID `{tid}` ({user_groups[tid]['group_name']})**:"
                    f" **YES** — Rank: `{user_groups[tid]['role']}`"
                )
              else:
                st.info(f"❌ **Group ID `{tid}`**: Not a member")

          # --- CHECK FRIENDS ---
          elif check_type == "Friends List":
            friends_url = f"https://friends.roblox.com/v1/users/{uid}/friends"
            f_resp = requests.get(friends_url)
            f_data = f_resp.json() if f_resp.status_code == 200 else {}

            user_friends = {f["id"] for f in f_data.get("data", [])}

            matches = 0
            for tid in target_ids:
              if tid in user_friends:
                matches += 1
                st.success(f"✅ **User ID `{tid}`**: **YES** — Friends!")
              else:
                st.info(f"❌ **User ID `{tid}`**: Not friends")

          # --- CHECK BADGES ---
          elif check_type == "Badge Ownership":
            owned_badges = {}
            chunk_size = 100
            for i in range(0, len(target_ids), chunk_size):
              chunk = target_ids[i : i + chunk_size]
              badge_ids_str = ",".join(map(str, chunk))
              badges_url = f"https://badges.roblox.com/v1/users/{uid}/badges/awarded-dates?badgeIds={badge_ids_str}"
              b_resp = requests.get(badges_url)
              if b_resp.status_code == 200:
                b_data = b_resp.json()
                for b_item in b_data.get("badgeAwardDates", []):
                  owned_badges[b_item["badgeId"]] = b_item["awardedDate"]

            matches = 0
            for tid in target_ids:
              if tid in owned_badges:
                matches += 1
                st.success(
                    f"✅ **Badge ID `{tid}`**: **YES** — Awarded on:"
                    f" `{owned_badges[tid]}`"
                )
              else:
                st.info(f"❌ **Badge ID `{tid}`**: Does not own")

          st.divider()
