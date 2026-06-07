import { useMemo, useState } from 'react';
import {
  Bell, Bot, Building2, ChartNoAxesCombined, ChevronLeft, CreditCard, Heart, Home, MapPin, MessageCircle, Mic, Package, Search, Settings, ShieldCheck, ShoppingBag, ShoppingCart, Star, Store as StoreIcon, Truck, User, Users, Wallet, X,
} from 'lucide-react';
import {
  Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { stores } from '../data/mock';
import type { Product, Store } from '../types/design';
import { money, km } from '../utils/design-format';
import { calculateShippingFee } from '../utils/design-shipping';
import '../design-style.css';

type Page = 'home' | 'search' | 'product' | 'cart' | 'orders' | 'owner' | 'admin' | 'chat';

const cx = (...classes: Array<string | false | null | undefined>) => classes.filter(Boolean).join(' ');

function useCart() {
  const [items, setItems] = useState<Array<{ storeId: string; productId: string; quantity: number }>>([]);
  const add = (storeId: string, productId: string) => {
    setItems((prev) => {
      const found = prev.find((item) => item.storeId === storeId && item.productId === productId);
      if (found) return prev.map((item) => item === found ? { ...item, quantity: item.quantity + 1 } : item);
      return [...prev, { storeId, productId, quantity: 1 }];
    });
  };
  const update = (storeId: string, productId: string, quantity: number) => {
    setItems((prev) => prev.map((item) => item.storeId === storeId && item.productId === productId ? { ...item, quantity: Math.max(1, quantity) } : item));
  };
  const remove = (storeId: string, productId: string) => setItems((prev) => prev.filter((item) => !(item.storeId === storeId && item.productId === productId)));
  const detailed = useMemo(() => items.map((item) => {
    const store = stores.find((s) => s.id === item.storeId)!;
    const product = store.products.find((p) => p.id === item.productId)!;
    return { ...item, store, product };
  }), [items]);
  const total = detailed.reduce((sum, item) => sum + item.product.price * item.quantity, 0);
  return { items, detailed, total, add, update, remove };
}

function PhoneFrame({ children, title }: { children: React.ReactNode; title?: string }) {
  return <div className="phone-frame">
    <div className="phone-status"><span>9:41</span><span>●●● 🔋</span></div>
    {title && <div className="phone-title">{title}</div>}
    {children}
  </div>;
}

function BottomNav({ page, setPage }: { page: Page; setPage: (p: Page) => void }) {
  const items: Array<[Page, React.ReactNode, string]> = [
    ['home', <Home size={18} />, 'Trang chủ'],
    ['search', <Search size={18} />, 'Tìm kiếm'],
    ['chat', <Bot size={22} />, 'Chat AI'],
    ['orders', <Package size={18} />, 'Đơn hàng'],
    ['cart', <ShoppingCart size={18} />, 'Giỏ hàng'],
  ];
  return <div className="bottom-nav">{items.map(([id, icon, label]) => <button key={id} onClick={() => setPage(id)} className={cx('nav-item', page === id && 'active')}>{icon}<span>{label}</span></button>)}</div>;
}

function Feature({ icon, label }: { icon: React.ReactNode; label: string }) { return <div className="feature-card">{icon}<span>{label}</span></div>; }

function DesignSystem() {
  const colors = ['#2563EB', '#F59E0B', '#10B981', '#EF4444', '#F8FAFC'];
  return <div className="design-card">
    <h3>Design System</h3>
    <div className="swatches">{colors.map((c) => <span key={c} style={{ background: c }} title={c} />)}</div>
    <div className="type-row"><b>Aa</b><div><strong>SF Pro / Inter</strong><small>Heading / Body / Caption</small></div></div>
    <div className="icon-row"><Home /><Search /><MessageCircle /><MapPin /><ShoppingCart /><User /><Settings /></div>
    <button className="primary-button full">Nút chính</button>
    <div className="ai-online"><Bot /> <span><b>AI Trợ lý</b><small>Đang online</small></span></div>
  </div>;
}

function HomePage({ setPage, openProduct }: { setPage: (p: Page) => void; openProduct: (p: Product) => void }) {
  return <PhoneFrame>
    <header className="mobile-header"><b>AI-SHOP.VN</b><Bell size={18} /></header>
    <button className="searchbar" onClick={() => setPage('search')}><Search size={17} /> Tìm thuốc, sản phẩm, cửa hàng gần bạn <Mic size={16} /></button>
    <div className="location-chip"><MapPin size={15} /> Quận 1, TP.HCM</div>
    <div className="category-row">{['Thuốc', 'Mỹ phẩm', 'Thực phẩm', 'Mẹ & Bé', 'Điện tử'].map((x) => <button key={x}>{x}</button>)}</div>
    <div className="ai-card"><Bot size={34} /><div><b>Chào bạn!</b><span>Bạn cần tìm sản phẩm gì gần đây?</span></div></div>
    <h3 className="section-title">Gợi ý tìm kiếm</h3>
    <div className="chips">{['Panadol', 'Vitamin C', 'Khẩu trang'].map((x) => <button key={x} onClick={() => setPage('search')}>{x}</button>)}</div>
    <TitleRow title="Cửa hàng nổi bật" />
    <div className="store-strip">{stores.map((s) => <div className="mini-store" key={s.id}><img src={s.coverImage} /><b>{s.name}</b><small>{km(s.distanceKm)}</small></div>)}</div>
    <TitleRow title="Sản phẩm gợi ý cho bạn" />
    <div className="product-grid">{stores[0].products.slice(0, 4).map((p) => <ProductTinyCard product={p} key={p.id} onClick={() => openProduct(p)} />)}</div>
    <BottomNav page="home" setPage={setPage} />
  </PhoneFrame>;
}

function SearchPage({ openProduct, openMap, addToCart, openStore, setPage }: { openProduct: (p: Product) => void; openMap: (s: Store) => void; addToCart: (sid: string, pid: string) => void; openStore: (s: Store) => void; setPage: (p: Page) => void }) {
  return <PhoneFrame title="Kết quả tìm kiếm">
    <div className="chat-bubble user">Tìm Panadol giảm đau gần đây</div>
    <div className="chat-bubble bot"><Bot size={18} /> Gần bạn có 3 cửa hàng phù hợp</div>
    <div className="filter-row"><button>&lt;500m</button><button>Còn hàng</button><button>Giá thấp → cao</button></div>
    <div className="result-list">{stores.map((store) => <StoreResultCard key={store.id} store={store} openProduct={openProduct} openMap={openMap} addToCart={addToCart} openStore={openStore} />)}</div>
    <div className="map-preview"><MapPin /> <span>Bản đồ cửa hàng gần bạn</span><button>Xem bản đồ</button></div>
    <BottomNav page="search" setPage={setPage} />
  </PhoneFrame>;
}

function StoreResultCard({ store, openProduct, openMap, addToCart, openStore }: { store: Store; openProduct: (p: Product) => void; openMap: (s: Store) => void; addToCart: (sid: string, pid: string) => void; openStore: (s: Store) => void }) {
  const product = store.products[0];
  return <article className="store-result">
    <img className="store-cover" src={store.coverImage} />
    <div className="store-info-row"><div><h4>{store.name}</h4><p><MapPin size={13} /> {store.address}</p></div><span className="distance">{km(store.distanceKm)}</span></div>
    <div className="product-row">
      <img src={product.image} />
      <div><b>{product.name}</b><small>{product.category} · {product.shelfLocation}</small><strong>{money(product.price)}</strong></div>
      <span className="stock">Còn {product.stock}</span>
    </div>
    <div className="action-row"><button onClick={() => openMap(store)} className="green">Chỉ đường</button><button onClick={() => openStore(store)}>Vào cửa hàng</button><button onClick={() => addToCart(store.id, product.id)} className="orange">Thêm</button><button onClick={() => openProduct(product)}>Chi tiết</button></div>
  </article>;
}

function ProductPage({ product, openMap, addToCart, setPage }: { product: Product; openMap: (s: Store) => void; addToCart: (sid: string, pid: string) => void; setPage: (p: Page) => void }) {
  const sellers = stores.filter((s) => s.products.some((p) => p.name === product.name || p.id === product.id));
  return <PhoneFrame title="Chi tiết sản phẩm">
    <img className="product-hero" src={product.image} />
    <h2 className="product-title">{product.name}</h2>
    <div className="rating"><Star size={16} fill="currentColor" /> {product.rating || 4.8} · 128 đánh giá <span className="stock">Còn {product.stock} {product.unit}</span></div>
    <div><span className="price-big">{money(product.price)}</span>{product.oldPrice && <span className="old-price">{money(product.oldPrice)}</span>}</div>
    <div className="fact-row"><span>Giảm đau hiệu quả</span><span>Hạ sốt</span><span>Không gây buồn ngủ</span></div>
    <TitleRow title="Cửa hàng có bán gần bạn" />
    {sellers.map((s) => {
      const p = s.products.find((x) => x.name === product.name || x.id === product.id)!;
      return <div className="seller-row" key={s.id}><StoreIcon size={18} /><div><b>{s.name}</b><small>{km(s.distanceKm)} · Còn {p.stock}</small></div><strong>{money(p.price)}</strong><button onClick={() => openMap(s)}>Map</button></div>;
    })}
    <div className="review-card"><b>Lan Anh ★★★★★</b><p>Hiệu quả giảm đau nhanh, dễ uống. Giao hàng đúng giờ.</p></div>
    <div className="sticky-actions"><button onClick={() => addToCart(stores[0].id, product.id)}>Thêm vào giỏ</button><button className="orange" onClick={() => setPage('cart')}>Mua ngay</button></div>
  </PhoneFrame>;
}

function CartPage({ cart, setPage }: { cart: ReturnType<typeof useCart>; setPage: (p: Page) => void }) {
  const shipping = calculateShippingFee(0.65, 900, cart.total);
  const discount = cart.total > 100000 ? 10000 : 0;
  const totalPay = cart.total + shipping - discount;
  return <PhoneFrame title="Giỏ hàng / Thanh toán">
    {cart.detailed.length === 0 ? <div className="empty"><ShoppingCart size={44} /><b>Giỏ hàng đang trống</b><button onClick={() => setPage('search')}>Tìm sản phẩm</button></div> : <>
      <div className="cart-list">{cart.detailed.map((item) => <div className="cart-item" key={item.productId}><img src={item.product.image} /><div><b>{item.product.name}</b><small>{item.store.name}</small><strong>{money(item.product.price)}</strong></div><div className="qty"><button onClick={() => cart.update(item.storeId, item.productId, item.quantity - 1)}>-</button><span>{item.quantity}</span><button onClick={() => cart.update(item.storeId, item.productId, item.quantity + 1)}>+</button></div><button onClick={() => cart.remove(item.storeId, item.productId)}><X size={14} /></button></div>)}</div>
      <CheckoutOptions />
      <div className="summary"><Row label="Tạm tính" value={money(cart.total)} /><Row label="Phí giao hàng" value={shipping === 0 ? 'Miễn phí' : money(shipping)} /><Row label="Giảm giá" value={`-${money(discount)}`} /><Row label="Tổng thanh toán" value={money(totalPay)} strong /></div>
      <button className="primary-button full" onClick={() => setPage('orders')}>Đặt hàng</button>
    </>}
  </PhoneFrame>;
}

function CheckoutOptions() { return <div className="checkout-card"><b>Phương thức nhận hàng</b><label><input type="radio" defaultChecked /> Nhận tại cửa hàng trong 30 phút</label><label><input type="radio" /> Giao tận nơi 1-2 giờ</label><b>Thanh toán</b><div className="payment-grid"><span><Wallet size={16} /> COD</span><span>Momo</span><span>ZaloPay</span><span><CreditCard size={16} /> Thẻ</span></div><div className="coupon"><input placeholder="Nhập mã giảm giá" /><button>Áp dụng</button></div></div>; }
function Row({ label, value, strong }: { label: string; value: string; strong?: boolean }) { return <div className={cx('summary-row', strong && 'strong')}><span>{label}</span><b>{value}</b></div>; }

function OrderPage() { return <PhoneFrame title="Theo dõi đơn hàng">
  <div className="order-card"><div className="order-head"><b>#ORD-2025-001234</b><span>Đang giao</span></div><small>Đặt lúc 09:41, 20/05/2025</small></div>
  <div className="timeline">{['Đã đặt hàng', 'Đã xác nhận', 'Đang chuẩn bị', 'Đang giao', 'Hoàn tất'].map((s, i) => <div className={cx('time-step', i < 4 && 'done')} key={s}><span /> <div><b>{s}</b><small>{i < 4 ? `10:${10 + i * 10}, 20/05/2025` : 'Dự kiến 11:30'}</small></div></div>)}</div>
  <div className="driver-card"><User /><div><b>Nguyễn Văn A</b><small>Đối tác: Ahamove · 11:30 - 12:00</small></div><button><MessageCircle size={16} /></button></div>
  <TitleRow title="Sản phẩm trong đơn" />
  {stores[0].products.slice(0, 2).map((p) => <div className="simple-row" key={p.id}><img src={p.image} /><div><b>{p.name}</b><small>x1</small></div><strong>{money(p.price)}</strong></div>)}
</PhoneFrame>; }

function ChatPage() { return <PhoneFrame title="Chat với cửa hàng">
  <div className="chat-center"><div className="chat-bubble bot">Xin chào, Nhà thuốc An Khang có thể hỗ trợ gì cho bạn?</div><div className="chat-bubble user">Shop còn Panadol Extra không?</div><div className="chat-bubble bot">Dạ còn 12 hộp. Bạn có thể nhận tại cửa hàng hoặc giao tận nơi.</div></div>
  <div className="message-input"><input placeholder="Nhập tin nhắn..." /><button>Gửi</button></div>
</PhoneFrame>; }

function OwnerDashboard() {
  const revenue = [{ d: '15/05', v: 5 }, { d: '16/05', v: 8 }, { d: '17/05', v: 6 }, { d: '18/05', v: 12 }, { d: '19/05', v: 10 }, { d: '20/05', v: 14 }];
  return <DesktopShell title="Owner Dashboard" menu={['Tổng quan', 'Đơn hàng', 'Sản phẩm', 'Kho hàng', 'Khuyến mãi', 'Khách hàng', 'Báo cáo']}>
    <KpiGrid items={[['Doanh thu', '12.450.000đ', '+18.6%'], ['Đơn hàng', '145', '+12.3%'], ['Lượt tìm kiếm', '1.285', '+15.7%'], ['Tồn kho', '320', '-5.2%']]} />
    <div className="dash-grid"><ChartCard title="Doanh thu"><ResponsiveContainer width="100%" height={180}><AreaChart data={revenue}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="d" /><YAxis /><Tooltip /><Area dataKey="v" stroke="#2563EB" fill="#DBEAFE" /></AreaChart></ResponsiveContainer></ChartCard><ChartCard title="Tỷ lệ đơn hàng"><ResponsiveContainer width="100%" height={180}><PieChart><Pie data={[{ name: 'Nhận tại cửa hàng', value: 60 }, { name: 'Giao tận nơi', value: 40 }]} dataKey="value"><Cell fill="#2563EB" /><Cell fill="#10B981" /></Pie></PieChart></ResponsiveContainer></ChartCard></div>
    <ProductTable />
  </DesktopShell>;
}

function AdminDashboard() { return <DesktopShell title="Admin Dashboard" menu={['Tổng quan', 'Người dùng', 'Cửa hàng', 'Sản phẩm', 'Đối soát dữ liệu', 'Danh mục', 'Báo cáo']}>
  <KpiGrid items={[['Users', '125.680', '+12.5%'], ['Stores', '8.432', '+8.3%'], ['GMV', '3.245.600.000đ', '+15.8%'], ['Reports', '128', '+6.2%']]} />
  <div className="admin-grid"><QueueCard title="Chờ duyệt cửa hàng" rows={['Nhà thuốc Minh Châu', 'Pharmacy Care', 'Kidsmart Store']} /><QueueCard title="Hàng đợi đối soát dữ liệu" rows={['Pharmacity - 1.256 sản phẩm', 'Nhà thuốc Long Châu - 1.102 sản phẩm', 'An Khang - 980 sản phẩm']} /><QueueCard title="Quản lý danh mục" rows={['Sức khỏe / Thuốc', 'Làm đẹp / Mỹ phẩm', 'Mẹ & Bé / Sữa']} /></div>
  <div className="activity-card"><b>Hoạt động gần đây</b>{['Duyệt cửa hàng Nhà thuốc Minh Châu', 'Hoàn thành đối soát Pharmacity', 'Xử lý báo cáo sản phẩm không hợp lệ'].map((r) => <p key={r}>10:45 · {r}</p>)}</div>
</DesktopShell>; }

function DesktopShell({ title, menu, children }: { title: string; menu: string[]; children: React.ReactNode }) { return <div className="desktop-shell"><aside><b>AI-SHOP.VN</b>{menu.map((m, i) => <button className={i === 0 ? 'active' : ''} key={m}>{m}</button>)}</aside><section><header><h2>{title}</h2><div><Bell size={18} /> Admin</div></header>{children}</section></div>; }
function KpiGrid({ items }: { items: string[][] }) { return <div className="kpi-grid">{items.map(([a, b, c]) => <div className="kpi-card" key={a}><span>{a}</span><b>{b}</b><small>{c}</small></div>)}</div>; }
function ChartCard({ title, children }: { title: string; children: React.ReactNode }) { return <div className="chart-card"><b>{title}</b>{children}</div>; }
function QueueCard({ title, rows }: { title: string; rows: string[] }) { return <div className="queue-card"><b>{title}</b>{rows.map((r) => <p key={r}>{r}<button>Duyệt</button></p>)}</div>; }
function ProductTable() { return <div className="table-card"><div className="table-head"><b>Quản lý sản phẩm</b><button>+ Thêm sản phẩm</button></div><table><tbody>{stores[0].products.map((p) => <tr key={p.id}><td><img src={p.image} /> {p.name}</td><td>{money(p.price)}</td><td>{p.stock}</td><td><span className="stock">Còn hàng</span></td><td>✎</td></tr>)}</tbody></table></div>; }

function StoreModal({ store, onClose, openProduct, addToCart, openMap }: { store: Store; onClose: () => void; openProduct: (p: Product) => void; addToCart: (sid: string, pid: string) => void; openMap: (s: Store) => void }) { return <div className="modal-backdrop"><div className="store-modal"><button className="modal-close" onClick={onClose}><X /></button><img className="modal-cover" src={store.coverImage} /><h2>{store.name}</h2><p><MapPin size={15} /> {store.address}</p><div className="modal-actions"><button onClick={() => openMap(store)}>Chỉ đường</button><button><MessageCircle size={16} /> Chat</button><button><Truck size={16} /> Ship</button></div><div className="product-grid modal-products">{store.products.map((p) => <ProductTinyCard key={p.id} product={p} onClick={() => openProduct(p)} action={<button onClick={(e) => { e.stopPropagation(); addToCart(store.id, p.id); }}>Thêm</button>} />)}</div></div></div>; }

function ProductTinyCard({ product, onClick, action }: { product: Product; onClick?: () => void; action?: React.ReactNode }) { return <button className="product-tiny" onClick={onClick}><img src={product.image} /><span>{product.name}</span><b>{money(product.price)}</b>{action}</button>; }
function TitleRow({ title }: { title: string }) { return <div className="title-row"><b>{title}</b><button>Xem tất cả</button></div>; }

export default function DesignPage() {
  const [page, setPage] = useState<Page>('home');
  const [selectedProduct, setSelectedProduct] = useState<Product>(stores[0].products[0]);
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);
  const cart = useCart();

  const openProduct = (product: Product) => { setSelectedProduct(product); setPage('product'); };
  const openMap = (store: Store) => window.open(`https://www.google.com/maps/dir/?api=1&destination=${store.latitude},${store.longitude}&q=${encodeURIComponent(store.name)}`, '_blank');

  return (
    <div className="app-shell">
      <section className="hero-panel">
        <aside className="brand-panel">
          <div className="brand-logo">AI-SHOP.VN ✨</div>
          <h1>AI trợ lý mua sắm & tìm cửa hàng gần bạn</h1>
          <p>Nền tảng AI giúp người dùng tìm sản phẩm uy tín gần nhất, so sánh giá, kiểm tra tồn kho và đặt mua nhanh chóng.</p>
          <div className="feature-grid">
            <Feature icon={<Bot />} label="AI thông minh" />
            <Feature icon={<MapPin />} label="Tìm gần bạn" />
            <Feature icon={<ChartNoAxesCombined />} label="So sánh giá" />
            <Feature icon={<ShieldCheck />} label="An toàn" />
          </div>
          <DesignSystem />
          <div className="dashboard-switcher">
            <button onClick={() => setPage('owner')}>Owner Dashboard</button>
            <button onClick={() => setPage('admin')}>Admin Dashboard</button>
          </div>
        </aside>

        <section className="preview-grid">
          {page === 'home' && <HomePage setPage={setPage} openProduct={openProduct} />}
          {page === 'search' && <SearchPage openProduct={openProduct} openMap={openMap} addToCart={cart.add} openStore={setSelectedStore} setPage={setPage} />}
          {page === 'product' && <ProductPage product={selectedProduct} openMap={openMap} addToCart={cart.add} setPage={setPage} />}
          {page === 'cart' && <CartPage cart={cart} setPage={setPage} />}
          {page === 'orders' && <OrderPage />}
          {page === 'chat' && <ChatPage />}
          {page === 'owner' && <OwnerDashboard />}
          {page === 'admin' && <AdminDashboard />}
        </section>
      </section>

      {selectedStore && <StoreModal store={selectedStore} onClose={() => setSelectedStore(null)} openProduct={openProduct} addToCart={cart.add} openMap={openMap} />}
      {cart.items.length > 0 && <button className="floating-cart" onClick={() => setPage('cart')}><ShoppingCart size={20} /> Giỏ hàng ({cart.items.length}) · {money(cart.total)}</button>}
    </div>
  );
}
