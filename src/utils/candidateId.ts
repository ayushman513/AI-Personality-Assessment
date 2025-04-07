/**
 * Generates a unique candidate ID using a combination of timestamp and random values
 * Format: prefix_timestamp_random
 * Example: CAND_20240315123456_abc123
 */
export function generateCandidateId(): string {
    const prefix = 'CAND';
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0];
    const randomStr = Math.random().toString(36).substring(2, 8);
    return `${prefix}_${timestamp}_${randomStr}`;
  }