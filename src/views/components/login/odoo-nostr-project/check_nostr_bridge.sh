#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}[OK]${NC} $2"
    else
        echo -e "${RED}[FAIL]${NC} $2"
    fi
}

echo "Running pre-update checks for nostr_bridge module..."

# 1. Verify required Python libraries
echo -e "\n${YELLOW}Checking required Python libraries...${NC}"
required_libs=("websockets" "nostr")
for lib in "${required_libs[@]}"; do
    if pip3 list | grep -F "$lib" > /dev/null; then
        print_status 0 "$lib is installed"
    else
        print_status 1 "$lib is not installed"
    fi
done

# 2. Check module file location
echo -e "\n${YELLOW}Checking module file location...${NC}"
module_path="/opt/odoo/custom_addons/nostr_bridge"
if [ -d "$module_path" ]; then
    print_status 0 "Module directory exists at $module_path"
    if [ -f "$module_path/__manifest__.py" ]; then
        print_status 0 "__manifest__.py file exists"
    else
        print_status 1 "__manifest__.py file not found in $module_path"
    fi
else
    print_status 1 "Module directory not found at $module_path"
fi

# 3. Check __manifest__.py content
echo -e "\n${YELLOW}Checking __manifest__.py content...${NC}"
manifest_file="$module_path/__manifest__.py"
if [ -f "$manifest_file" ]; then
    if grep -q "'depends':" "$manifest_file" && grep -q "'data':" "$manifest_file"; then
        print_status 0 "__manifest__.py contains 'depends' and 'data' sections"
    else
        print_status 1 "__manifest__.py might be missing 'depends' or 'data' sections"
    fi
else
    print_status 1 "__manifest__.py file not found"
fi

# 4. Verify configuration parameters
echo -e "\n${YELLOW}Checking configuration parameters...${NC}"
odoo_db="odoodb"  # Replace with your actual database name if different
config_param="git_nostr_bridge.relay_urls"
relay_urls=$(psql -d $odoo_db -t -c "SELECT value FROM ir_config_parameter WHERE key='$config_param';")
if [ -n "$relay_urls" ]; then
    print_status 0 "Relay URLs are set: $relay_urls"
else
    print_status 1 "Relay URLs are not set in the database"
fi

# 5. Test network connectivity
echo -e "\n${YELLOW}Testing network connectivity...${NC}"
test_urls=("wss://nostr-pub.wellorder.net" "wss://relay.nostr.info" "wss://nostr.zebedee.cloud")
for url in "${test_urls[@]}"; do
    if curl --output /dev/null --silent --head --fail "$url"; then
        print_status 0 "Connection to $url successful"
    else
        print_status 1 "Failed to connect to $url"
    fi
done

echo -e "\n${YELLOW}Pre-update checks completed.${NC}"
