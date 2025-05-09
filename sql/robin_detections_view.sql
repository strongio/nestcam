CREATE OR REPLACE VIEW robin_detections AS
SELECT
    filename,
    endpoint_id,
    label_name,
    confidence,
    bboxes,
    event_id,
    -- Properly combine date and time
    TIMESTAMP_FROM_PARTS(
        dt_year, dt_month, dt_day,
        dt_hour, dt_minute, dt_second
    ) AS detected_at
FROM VIDEO_STREAM_INFERENCE
WHERE label_name = 'robin'
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY confidence DESC) = 1;

-- Query the view to see all inference results
SELECT * FROM robin_detections;