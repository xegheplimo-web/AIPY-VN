import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { MapPin, ShoppingCart, Star, Clock, Phone, MessageCircle, Navigation, Heart } from 'lucide-react';

const sampleStores = [
  {
    id: '1',
    name: 'Nha thuoc An Khang',
    address: '123 Nguyen Trai, Quan 1',
    distance: 350,
    rating: 4.5,
    reviews: 128,
    isOpen: true,
    products: [
      { name: 'Panadol Extra 500mg', price: 35000, stock: 12, shelf: 'Ke A-12' },
      { name: 'Vitamin C 1000mg', price: 85000, stock: 5, shelf: 'Ke B-03' },
    ],
  },
  {
    id: '2',
    name: 'Pharmacity Nguyen Van Cu',
    address: '456 Nguyen Van Cu, Quan 5',
    distance: 820,
    rating: 4.2,
    reviews: 89,
    isOpen: true,
    products: [
      { name: 'Panadol Extra 500mg', price: 32000, stock: 8, shelf: 'Ke C-05' },
      { name: 'Omeprazole 20mg', price: 45000, stock: 20, shelf: 'Ke D-01' },
    ],
  },
  {
    id: '3',
    name: 'Nha thuoc Long Chau',
    address: '78 Le Loi, Quan 3',
    distance: 1200,
    rating: 4.8,
    reviews: 256,
    isOpen: false,
    products: [
      { name: 'Panadol Extra 500mg', price: 33000, stock: 0, shelf: 'Ke A-08' },
    ],
  },
];

function StoreCard({ store }: { store: typeof sampleStores[0] }) {
  const [liked, setLiked] = useState(false);

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12 border-2 border-primary/10">
              <AvatarImage src={`https://apiService.dicebear.com/7.x/initials/svg?seed=${store.name}`} />
              <AvatarFallback className="bg-primary/10 text-primary text-sm">
                {store.name.split(' ').map(w => w[0]).join('').slice(0, 2)}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle className="text-base">{store.name}</CardTitle>
              <CardDescription className="flex items-center gap-1 mt-0.5">
                <MapPin className="w-3 h-3" />
                {store.address}
              </CardDescription>
            </div>
          </div>
          <button
            onClick={() => setLiked(!liked)}
            className="p-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            <Heart className={`w-5 h-5 ${liked ? 'fill-red-500 text-red-500' : 'text-gray-400'}`} />
          </button>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <div className="flex items-center gap-2 mb-3">
          <Badge variant={store.distance < 500 ? 'default' : store.distance < 1000 ? 'secondary' : 'outline'}>
            <Navigation className="w-3 h-3 mr-1" />
            {(store.distance / 1000).toFixed(1)}km
          </Badge>
          <Badge variant="outline" className="gap-1">
            <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
            {store.rating} ({store.reviews})
          </Badge>
          <Badge variant={store.isOpen ? 'default' : 'destructive'}>
            <Clock className="w-3 h-3 mr-1" />
            {store.isOpen ? 'Dang mo cua' : 'Da dong cua'}
          </Badge>
        </div>

        <div className="space-y-2">
          {store.products.map((p, i) => (
            <div key={i} className="flex items-center justify-between p-2.5 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium">{p.name}</p>
                <p className="text-xs text-gray-500">Ke: {p.shelf}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-primary">{p.price.toLocaleString('vi-VN')}d</p>
                <Badge variant={p.stock > 0 ? 'default' : 'destructive'} className="text-xs">
                  {p.stock > 0 ? `Con ${p.stock}` : 'Hết hàng'}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>

      <CardFooter className="flex gap-2 pt-0">
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" className="flex-1 gap-1.5">
              <Phone className="w-4 h-4" />
              Lien he
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{store.name}</DialogTitle>
              <DialogDescription>
                Thong tin lien he cua cua hang
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-4">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <Phone className="w-5 h-5 text-primary" />
                <div>
                  <p className="text-sm font-medium">Dien thoai</p>
                  <p className="text-sm text-gray-500">1900 1234 56</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <MapPin className="w-5 h-5 text-primary" />
                <div>
                  <p className="text-sm font-medium">Dia chi</p>
                  <p className="text-sm text-gray-500">{store.address}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button onClick={() => toast.success('Da sao chep so dien thoai!')}>
                Sao chep SDT
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Button
          className="flex-1 gap-1.5"
          onClick={() => toast.success(`Da them vao gio hang tu ${store.name}`)}
        >
          <ShoppingCart className="w-4 h-4" />
          Mua ngay
        </Button>
      </CardFooter>
    </Card>
  );
}

export default function DemoPage() {
  const [loading, setLoading] = useState(false);

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      toast.success('Da cap nhat ket qua tim kiem!');
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-white border-b">
        <div className="max-w-2xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold">VietStore RAG</h1>
              <p className="text-sm text-gray-500">Tim kiem san pham gan day bang AI</p>
            </div>
            <Badge variant="outline" className="gap-1">
              <MapPin className="w-3 h-3" />
              Quan 1, TP.HCM
            </Badge>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              className="flex-1 justify-start gap-2 text-gray-500"
              onClick={() => toast.info('Mo chat search...')}
            >
              <MessageCircle className="w-4 h-4" />
              Tim Panadol gan day...
            </Button>
            <Button size="icon" onClick={handleRefresh} disabled={loading}>
              {loading ? (
                <Skeleton className="h-4 w-4 rounded-full" />
              ) : (
                <Navigation className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-4">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <Card className="text-center py-3">
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-primary">3</p>
              <p className="text-xs text-gray-500">Cua hang</p>
            </CardContent>
          </Card>
          <Card className="text-center py-3">
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-emerald-500">5</p>
              <p className="text-xs text-gray-500">Sản phẩm</p>
            </CardContent>
          </Card>
          <Card className="text-center py-3">
            <CardContent className="p-0">
              <p className="text-2xl font-bold text-amber-500">350m</p>
              <p className="text-xs text-gray-500">Gan nhat</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="stores" className="mb-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="stores">Cua hang</TabsTrigger>
            <TabsTrigger value="products">Sản phẩm</TabsTrigger>
            <TabsTrigger value="map">Ban do</TabsTrigger>
          </TabsList>

          <TabsContent value="stores" className="mt-4 space-y-4">
            {loading ? (
              <>
                <Skeleton className="h-48 w-full rounded-xl" />
                <Skeleton className="h-48 w-full rounded-xl" />
              </>
            ) : (
              sampleStores.map((store) => (
                <StoreCard key={store.id} store={store} />
              ))
            )}
          </TabsContent>

          <TabsContent value="products" className="mt-4">
            <ScrollArea className="h-[500px]">
              <div className="space-y-3">
                {sampleStores.flatMap(s => s.products.map((p, i) => ({ ...p, store: s.name, id: `${s.id}-${i}` }))).map((p) => (
                  <Card key={p.id}>
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="font-medium">{p.name}</p>
                        <p className="text-xs text-gray-500">{p.store} - {p.shelf}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-primary">{p.price.toLocaleString('vi-VN')}d</p>
                        <Button size="sm" className="mt-1" onClick={() => toast.success(`Da them ${p.name}`)}>
                          Them
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="map" className="mt-4">
            <Card className="h-[400px] flex items-center justify-center bg-gray-100">
              <div className="text-center text-gray-400">
                <MapPin className="w-12 h-12 mx-auto mb-2" />
                <p>Ban do Google Maps se hien thi o day</p>
              </div>
            </Card>
          </TabsContent>
        </Tabs>

        <Separator className="my-4" />

        {/* Toast Demo Buttons */}
        <div className="flex flex-wrap gap-2">
          <Button variant="default" onClick={() => toast.success('Thanh cong!')}>Toast Success</Button>
          <Button variant="destructive" onClick={() => toast.error('Co loi xay ra!')}>Toast Error</Button>
          <Button variant="outline" onClick={() => toast.info('Thong bao')}>Toast Info</Button>
          <Button variant="secondary" onClick={() => toast.warning('Canh bao')}>Toast Warning</Button>
        </div>
      </div>
    </div>
  );
}
