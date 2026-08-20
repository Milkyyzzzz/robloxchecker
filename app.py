import re
import requests
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Roblox Multi-Checker", page_icon="🔍", layout="centered"
)

st.title("🔍 Roblox Multi-Target Checker")
st.write(
    "Check if a user belongs to specific groups, is friends with specific"
    " users, or owns specific badges by pasting a bulk list of IDs!"
)

# Selection for what to check
check_type = st.selectbox(
    "Select What to Check:",
    ["Groups Membership", "Friends List", "Badge Ownership"],
)

# User Inputs
username_input = st.text_input(
    "Roblox Username to Check",
    "Roblox",
    help="Enter the username of the player you want to scan.",
)

raw_ids_input = st.text_area(
    "Paste Raw IDs (separated by commas, spaces, or newlines)",
    placeholder="193417234, 129347192384, 129347\n98412374\n123456",
    help=(
        "Paste a batch of IDs here. They can be separated by commas, spaces,"
        " or new lines."
    ),
)


def parse_ids(raw_text):
  if not raw_text:
    return []
  # Extract all numbers from the text block automatically
  id_strings = re.findall(r"\d+", raw_text)
  return [int(i) for i in id_strings]


if st.button("Run Check", type="primary"):
  target_ids = parse_ids(raw_ids_input)

  if not username_input.strip():
    st.warning("Please enter a valid Roblox username.")
  elif not target_ids:
    st.warning(
        "Please enter or paste at least one valid ID in the text area above."
    )
  else:
    with st.spinner(f"Looking up user '{username_input}'..."):
      # Step 1: Convert Username to User ID
      user_lookup_url = "https://users.roblox.com/v1/usernames/users"
      payload = {"usernames": [username_input], "excludeBannedUsers": True}

      try:
        response = requests.post(user_lookup_url, json=payload)
        data = response.json()

        if not data.get("data"):
          st.error(
              f"User '{username_input}' could not be found. Check the spelling."
          )
        else:
          user_id = data["data"][0]["id"]
          display_name = data["data"][0]["displayName"]

          st.success(
              f"Found User: **{display_name}** (`{username_input}` | ID:"
              f" `{user_id}`)"
          )
          st.divider()

          # --- CHECK GROUPS ---
          if check_type == "Groups Membership":
            st.subheader("🛡️ Group Results")
            groups_url = (
                f"https://groups.roblox.com/v2/users/{user_id}/groups/roles"
            )
            g_resp = requests.get(groups_url)
            g_data = g_resp.json()

            user_groups = {}
            for item in g_data.get("data", []):
              g_id = item["group"]["id"]
              g_name = item["group"]["name"]
              r_name = item["role"]["name"]
              user_groups[g_id] = {"group_name": g_name, "role": r_name}

            matches_found = 0
            for tid in target_ids:
              if tid in user_groups:
                matches_found += 1
                st.success(
                    f"✅ **Group ID `{tid}` ({user_groups[tid]['group_name']})**:"
                    f" **YES** — Rank: `{user_groups[tid]['role']}`"
                )
              else:
                st.info(f"❌ **Group ID `{tid}`**: NO (Not a member)")

            st.caption(
                f"Checked {len(target_ids)} IDs. Found {matches_found} matches."
            )

          # --- CHECK FRIENDS ---
          elif check_type == "Friends List":
            st.subheader("👥 Friend Results")
            friends_url = f"https://friends.roblox.com/v1/users/{user_id}/friends"
            f_resp = requests.get(friends_url)
            f_data = f_resp.json()

            user_friends = set()
            for friend in f_data.get("data", []):
              user_friends.add(friend["id"])

            matches_found = 0
            for tid in target_ids:
              if tid in user_friends:
                matches_found += 1
                st.success(
                    f"✅ **User ID `{tid}`**: **YES** — They are friends!"
                )
              else:
                st.info(f"❌ **User ID `{tid}`**: NO (Not friends)")

            st.caption(
                f"Checked {len(target_ids)} IDs. Found {matches_found} matches."
            )

          # --- CHECK BADGES ---
          elif check_type == "Badge Ownership":
            st.subheader("🏅 Badge Results")
            owned_badges = {}
            chunk_size = 100
            for i in range(0, len(target_ids), chunk_size):
              chunk = target_ids[i : i + chunk_size]
              badge_ids_str = ",".join(map(str, chunk))
              badges_url = f"https://badges.roblox.com/v1/users/{user_id}/badges/awarded-dates?badgeIds={badge_ids_str}"
              b_resp = requests.get(badges_url)
              if b_resp.status_code == 200:
                b_data = b_resp.json()
                for b_item in b_data.get("badgeAwardDates", []):
                  owned_badges[b_item["badgeId"]] = b_item["awardedDate"]

            matches_found = 0
            for tid in target_ids:
              if tid in owned_badges:
                matches_found += 1
                st.success(
                    f"✅ **Badge ID `{tid}`**: **YES** — Awarded on:"
                    f" `{owned_badges[tid]}`"
                )
              else:
                st.info(f"❌ **Badge ID `{tid}`**: NO (Does not own badge)")

            st.caption(
                f"Checked {len(target_ids)} IDs. Found {matches_found} matches."
            )

      except Exception as e:
        st.error(f"An error occurred while querying the Roblox API: {e}")
