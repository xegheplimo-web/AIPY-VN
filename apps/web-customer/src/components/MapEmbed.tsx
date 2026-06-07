interface MapEmbedProps {
  latitude: number;
  longitude: number;
  name?: string;
  height?: string;
}

export default function MapEmbed({ latitude, longitude, name = "", height = "300px" }: MapEmbedProps) {
  const encodedName = encodeURIComponent(name);
  const mapSrc = `https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d1000!2d${longitude}!3d${latitude}!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2z${encodedName}!5e0!3m2!1svi!2sus!4v1`;

  return (
    <div className="w-full rounded-xl overflow-hidden border" style={{ height }}>
      <iframe
        title={name || "Map"}
        src={mapSrc}
        width="100%"
        height="100%"
        style={{ border: 0 }}
        allowFullScreen
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
      />
    </div>
  );
}
