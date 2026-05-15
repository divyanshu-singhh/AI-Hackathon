# CSV Input Format

Use these columns:

```csv
image_name,image_url,expected_category,notes
sample1.jpg,https://example.com/sample1.jpg,Furniture,Wooden chair
sample2.jpg,https://example.com/sample2.jpg,Industrial Pump,Contains label text
```

`image_url` must be a publicly reachable image URL. `expected_category` is optional and helps compare predicted metadata during demos.
