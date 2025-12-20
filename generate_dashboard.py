#!/usr/bin/env python3
"""
Generate HTML dashboard from campaign test results.
"""
import json
import os

def generate_dashboard():
    """Generate dashboard HTML from campaign output data."""

    # Read campaign data
    output_path = os.path.join(os.path.dirname(__file__), "data", "outputs", "campaign_ids.json")

    if not os.path.exists(output_path):
        print("Error: Campaign output file not found. Run tests first.")
        return

    with open(output_path, "r") as f:
        campaign_data = json.load(f)

    # Read HTML template
    template_path = os.path.join(os.path.dirname(__file__), "reports", "dashboard.html")

    with open(template_path, "r") as f:
        html_content = f.read()

    # Inject campaign data into template
    html_content = html_content.replace(
        "CAMPAIGN_DATA_PLACEHOLDER",
        json.dumps(campaign_data, indent=2)
    )

    # Write generated dashboard
    dashboard_path = os.path.join(os.path.dirname(__file__), "reports", "campaign_dashboard.html")

    with open(dashboard_path, "w") as f:
        f.write(html_content)

    print(f"Dashboard generated: {dashboard_path}")
    print(f"\nCampaign Summary:")
    print(f"  - Campaign Number: {campaign_data.get('campaignNumber', 'N/A')}")
    print(f"  - Campaign Name: {campaign_data.get('campaignName', 'N/A')}")
    print(f"  - Total Projects: {campaign_data.get('totalCount', 0)}")
    print(f"  - Total Facilities: {campaign_data.get('facilityCount', 0)}")
    print(f"  - Total Staff: {campaign_data.get('staffCount', 0)}")
    print(f"  - Boundary Types: {len(campaign_data.get('projectsByBoundaryType', {}))}")

    return dashboard_path


if __name__ == "__main__":
    generate_dashboard()
