---
title: "Sync Providers"
order: 3
---

# Sync Providers

After connecting your billing data providers, you need to manually sync their data into NarevAI for analysis. This guide explains how to trigger and manage your billing data synchronization.

## How Data Sync Works

NarevAI uses **manual synchronization** - you trigger data imports when needed rather than on a schedule. This gives you full control over when and what data to import.

### Sync Process:
1. **Connect Provider** - Link your cloud account ([see provider guides](../connect-providers/))
2. **Trigger Sync** - Manually start data import  
3. **Monitor Progress** - Track sync status and results
4. **Retry if Needed** - Handle any failed synchronizations

## Starting a Data Sync

### 1. Navigate to Data Sync

1. In the NarevAI sidebar, under **Data Connections**, click **Sync**
2. You'll see the sync management interface with three main sections:
   - **Primary Actions**: Health Check, Refresh, Trigger Sync
   - **Sync History Table**: All previous sync runs
   - **Action Menus**: Details, retry, cancel options per sync

### 2. Trigger New Sync

1. Click the **Trigger Sync** button
2. In the sync configuration dialog, set:

   **Provider (Optional)**
   - Choose specific provider (AWS, Azure, GCP, OpenAI) or leave empty for all

   **Date Range Options:**
   - **Days Back**: Number of days to sync backwards (default: 30, range: 1-365)
   - **OR Custom Range**: Set specific start and end dates

3. Click **Start Sync** to begin the process

::: tip Sync Duration
Syncs can take several minutes to hours depending on:
- Amount of historical data requested
- Provider data availability and processing speed
- Number of providers being synced simultaneously
:::

## Monitoring Sync Status

### Sync Run Table Columns:

- **Run ID**: Unique identifier (first 8 characters shown)
- **Provider**: Which provider is being synced
- **Status**: Current sync state with colored badges
- **Started**: When the sync began (relative time)
- **Duration**: How long the sync took/is taking
- **Records**: Count of processed, created, and updated records

### Status Types:

- **Pending** (gray) - Queued for execution
- **Running** (blue) - Currently importing data
- **Completed** (green) - Successfully finished
- **Failed** (red) - Encountered errors
- **Cancelled** (gray) - Manually stopped

## Managing Sync Runs

### Available Actions:

For each sync run, you can:

- **View Details** - See comprehensive run information
- **Copy Run ID** - Copy identifier to clipboard
- **Retry Sync** - Re-run failed or cancelled syncs
- **Cancel Sync** - Stop running or pending syncs

### Action Availability:
- **Retry**: Only available for failed or cancelled runs
- **Cancel**: Only available for running or pending runs
- **View Details**: Always available

## Troubleshooting Sync Issues

### Common Problems:

**Sync Fails Immediately**
- Check provider credentials haven't expired
- Verify network connectivity
- Ensure provider permissions are still valid

**No Data Found**
- Confirm billing data exists in provider for requested date range
- Check if exports are properly configured (24-48 hour delay is normal)
- Verify account access to billing information

**Partial Data Import**
- Review detailed error messages in sync details
- Try smaller date ranges to isolate issues
- Check provider-specific limits and quotas

**Sync Takes Too Long**
- Reduce the date range being synced
- Check provider API rate limits
- Monitor system resources

### Getting Help:

1. **View Sync Details** - Click on any sync run for comprehensive information
2. **Check Health Status** - Use the Health Check button to verify sync service
3. **Review Error Messages** - Failed syncs show specific error details
4. **Provider Troubleshooting** - Reference individual provider guides for specific issues

## Data Import Frequency

Since syncs are manual, consider these guidelines:

- **Initial Setup**: Import 30-90 days of historical data
- **Regular Updates**: Weekly or bi-weekly syncs for recent data
- **Analysis Prep**: Sync before important cost reviews
- **Issue Investigation**: On-demand syncs when investigating cost spikes

## Next Steps

After successful data synchronization:

1. **Verify Data** - Check that expected records were imported
2. **Explore Analytics** - Navigate to cost analysis dashboards  
3. **Set Baselines** - Establish cost benchmarks from imported data
4. **Plan Regular Syncs** - Decide on your manual sync frequency

Your billing data is now ready for analysis in NarevAI!
