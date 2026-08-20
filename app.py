import requests
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="Roblox Group Checker", page_icon="🎮", layout="centered"
)

st.title("🎮 Roblox Group Membership Checker")
st.write(
    "Enter a Roblox username and a Group ID to check if they are a member"
    " and see their rank."
)

# User Inputs
username_input = st.text_input("Roblox Username", "Roblox")
target_group_id = st.number_input(
    "Target Group ID", min_value=1, value=1200769, step=1
)

if st.button("Check Membership", type="primary"):
  if not username_input.strip():
    st.warning("Please enter a valid username.")
  else:
    with st.spinner(f"Looking up {username_input}..."):
      # Step 1: Convert Username to User ID
      user_lookup_url = "https://users.roblox.com/v1/usernames/users"
      payload = {"usernames": [username_input], "excludeBannedUsers": True}

      try:
        response = requests.post(user_lookup_url, json=payload)
        data = response.json()

        if not data.get("data"):
          st.error(
              f"User '{username_input}' could not be found. Please check the"
              " spelling."
          )
        else:
          user_id = data["data"][0]["id"]
          display_name = data["data"][0]["displayName"]

          # Step 2: Fetch groups the user belongs to
          groups_url = f"https://groups.roblox.com/v2/users/{user_id}/groups/roles"
          groups_response = requests.get(groups_url)
          groups_data = groups_response.json()

          found = False
          role_name = ""

          for item in groups_data.get("data", []):
            if item["group"]["id"] == int(target_group_id):
              found = True
              role_name = item["role"]["name"]
              break

          # Step 3: Display the results nicely
          st.divider()
          if found:
            st.success(
                f"**Match Found!**\n\n- **User:** {display_name}"
                f" (`{username_input}`)\n- **User ID:** `{user_id}`\n- **Group"
                f" Rank:** `{role_name}`"
            )
          else:
            st.info(
                f"**Not a Member**\n\n- **User:** {display_name}"
                f" (`{username_input}`)\n- **User ID:** `{user_id}`\n- **Status:**"
                f" Not in Group ID `{target_group_id}`"
            )

      except Exception as e:
        st.error(f"An error occurred while connecting to the Roblox API: {e}")
