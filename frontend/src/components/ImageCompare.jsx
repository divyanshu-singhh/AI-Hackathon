export default function ImageCompare({ result }) {
  const images = [
    ["Original", result?.original_image_url],
    ["Background Removed", result?.background_removed_image_url],
    ["Final Image", result?.rebuilt_image_url]
  ].filter(([, url]) => Boolean(url));

  if (!images.length) {
    return <div className="empty-image">No image output yet</div>;
  }

  return (
    <div className="image-compare">
      {images.map(([label, url]) => (
        <figure key={label}>
          <img src={url} alt={`${label} product`} />
          <figcaption>{label}</figcaption>
        </figure>
      ))}
    </div>
  );
}
