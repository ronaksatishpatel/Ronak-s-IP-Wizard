import streamlit as st
import ipaddress
import math
import pandas as pd

st.set_page_config(page_title="Subnet Calculator with Explanation", layout="centered")
st.title("📡 Subnet Calculator with Full Explanation")

# --------- INITIALIZE SESSION STATE ---------
# We initialize the keys to empty strings so they start blank
if "base_net" not in st.session_state:
    st.session_state["base_net"] = ""
if "s_count" not in st.session_state:
    st.session_state["s_count"] = ""

# --------- RESET LOGIC ---------
def clear_form():
    # Setting both to empty strings clears the fields entirely
    st.session_state["base_net"] = ""
    st.session_state["s_count"] = ""

# Add the Reset button with the callback
st.button("🔄 Reset All Fields", on_click=clear_form)

# --------- INPUTS ---------
# We use text_input for both so that they can be truly blank
base_network_input = st.text_input(
    "1️⃣ Enter base network (e.g., 10.0.0.0/8)", 
    key="base_net",
    placeholder="e.g. 192.168.1.0/24"
)

subnet_count_raw = st.text_input(
    "2️⃣ How many subnets to list?", 
    key="s_count",
    placeholder="e.g. 8"
)

# --------- CALCULATIONS ---------
# Only proceed if both fields have values
if base_network_input.strip() != "" and subnet_count_raw.strip() != "":
    try:
        # Convert the string input back to a number for calculation
        subnet_count = int(subnet_count_raw)
        if subnet_count < 1:
            st.error("❌ Please enter a number greater than 0 for subnets.")
            st.stop()
            
        network = ipaddress.ip_network(base_network_input, strict=False)
        original_prefix = network.prefixlen

        # 1. Determine how many bits to borrow
        bits_borrowed = math.ceil(math.log2(subnet_count))
        new_prefix = original_prefix + bits_borrowed

        if new_prefix > 32:
            st.error("❌ Cannot create that many subnets. The prefix would exceed /32.")
        else:
            # 2. New Subnet Mask
            subnet_mask = ipaddress.IPv4Network(f"0.0.0.0/{new_prefix}").netmask.exploded

            # 3. Subnet Increment
            octets = subnet_mask.split(".")
            if new_prefix > 24:
                increment = 256 - int(octets[3])
                octet_level = "4th"
            elif new_prefix > 16:
                increment = 256 - int(octets[2])
                octet_level = "3rd"
            elif new_prefix > 8:
                increment = 256 - int(octets[1])
                octet_level = "2nd"
            else:
                increment = 256 - int(octets[0])
                octet_level = "1st"

            # 4. Hosts per Subnet
            host_bits = 32 - new_prefix
            total_hosts = 2 ** host_bits
            usable_hosts = max(0, total_hosts - 2)

            # --------- SUBNETTING CALCULATIONS SECTION ---------
            st.subheader("📘 Subnetting Calculations")

            st.markdown(f"**1. Original CIDR Prefix:** /{original_prefix}  \n"
                        f"> The starting network mask provided in the input.")

            st.markdown(f"**2. New Subnet Prefix (CIDR):** /{new_prefix}  \n"
                        f"> Since we need at least {subnet_count} subnets, we find the smallest power of 2 ≥ {subnet_count}.  \n"
                        f"> 2^{bits_borrowed} = {2 ** bits_borrowed}, so we borrow {bits_borrowed} bits from the host portion.")

            st.markdown(f"**3. Bits Borrowed:** {bits_borrowed}  \n"
                        f"> These bits increase the subnet count from 1 to {2 ** bits_borrowed}.")

            st.markdown(f"**4. Subnet Mask:** {subnet_mask}  \n"
                        f"> Equivalent to /{new_prefix}, giving each subnet its boundary and size.")

            st.markdown(f"**5. Subnet Increment:** {increment} (in the {octet_level} octet)  \n"
                        f"> This tells us how far apart each subnet’s network address is from the next.")

            st.markdown(f"**6. Usable Hosts per Subnet:** {usable_hosts}  \n"
                        f"> Each subnet has 2^{host_bits} addresses. Minus network and broadcast, that’s {usable_hosts} usable hosts.")

            # --------- OPTIONAL: Show Subnet Table ---------
            st.divider()
            st.subheader("📊 Example: First N Subnets")

            subnets = list(network.subnets(new_prefix=new_prefix))
            max_available = len(subnets)

            if subnet_count > max_available:
                st.warning(f"Note: Only {max_available} subnets can be created from this network. Showing all available.")
                display_count = max_available
            else:
                display_count = subnet_count

            rows = []
            for i in range(display_count):
                net = subnets[i]
                usable_start = net.network_address + 1 if net.num_addresses > 2 else "N/A"
                usable_end = net.broadcast_address - 1 if net.num_addresses > 2 else "N/A"
                
                rows.append({
                    "Subnet #": i + 1,
                    "Network": str(net.network_address),
                    "Usable Start": str(usable_start),
                    "Usable End": str(usable_end),
                    "Broadcast": str(net.broadcast_address),
                    "Total Addresses": net.num_addresses
                })

            df = pd.DataFrame(rows)
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Subnet Table as CSV", csv, file_name="subnet_table.csv")

    except ValueError as e:
        if "invalid literal for int()" in str(e):
             st.error("❌ Please enter a whole number for the subnet count.")
        else:
             st.info("💡 Please enter a valid IPv4 network (e.g., 192.168.1.0/24) to begin.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
else:
    st.info("👋 Welcome! Enter a network address and the number of subnets to get started.")
