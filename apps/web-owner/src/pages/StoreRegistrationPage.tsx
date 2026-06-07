import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronLeft, Check } from 'lucide-react';
import api from '../services/api';

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

export default function StoreRegistrationPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    name: '',
    category: '',
    phone: '',
    email: '',
    address: '',
    latitude: '',
    longitude: '',
    businessHours: {} as Record<string, string>,
  });
  const [submitting, setSubmitting] = useState(false);

  const updateField = (field: string, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await api.post('/stores/register', form);
      navigate('/dashboard');
    } catch (err) {
      alert('Dang ky that bai, vui long thu lai!');
    } finally {
      setSubmitting(false);
    }
  };

  const steps = [
    { title: 'Thong tin cua hang', fields: (
      <div className="space-y-4">
        <input value={form.name} onChange={(e) => updateField('name', e.target.value)} placeholder="Ten cua hang" className="w-full px-4 py-3 border rounded-lg" required />
        <input value={form.category} onChange={(e) => updateField('category', e.target.value)} placeholder="Nganh hang" className="w-full px-4 py-3 border rounded-lg" />
        <input value={form.phone} onChange={(e) => updateField('phone', e.target.value)} placeholder="So dien thoai" className="w-full px-4 py-3 border rounded-lg" />
        <input value={form.email} onChange={(e) => updateField('email', e.target.value)} placeholder="Email" className="w-full px-4 py-3 border rounded-lg" />
      </div>
    )},
    { title: 'Dia chi', fields: (
      <div className="space-y-4">
        <textarea value={form.address} onChange={(e) => updateField('address', e.target.value)} placeholder="Dia chi day du" className="w-full px-4 py-3 border rounded-lg" rows={3} />
        <div className="grid grid-cols-2 gap-4">
          <input value={form.latitude} onChange={(e) => updateField('latitude', e.target.value)} placeholder="Vi do (lat)" className="w-full px-4 py-3 border rounded-lg" />
          <input value={form.longitude} onChange={(e) => updateField('longitude', e.target.value)} placeholder="Kinh do (lng)" className="w-full px-4 py-3 border rounded-lg" />
        </div>
      </div>
    )},
    { title: 'Gio mo cua', fields: (
      <div className="space-y-3">
        {DAYS.map((day) => (
          <div key={day} className="flex items-center gap-3">
            <span className="w-24 capitalize text-sm">{day}</span>
            <input
              value={form.businessHours[day] || ''}
              onChange={(e) => setForm(prev => ({ ...prev, businessHours: { ...prev.businessHours, [day]: e.target.value } }))}
              placeholder="08:00 - 22:00"
              className="flex-1 px-3 py-2 border rounded-lg"
            />
          </div>
        ))}
      </div>
    )},
    { title: 'Hoan tat', fields: (
      <div className="text-center py-8">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-green-600" />
        </div>
        <h3 className="text-lg font-bold mb-2">San sang dang ky!</h3>
        <p className="text-gray-500">Kiem tra thong tin va xac nhan</p>
      </div>
    )},
  ];

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center mb-6">
          <button onClick={() => navigate('/login')} className="p-2 hover:bg-gray-100 rounded-full">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h1 className="text-xl font-bold ml-2">Dang ky cua hang</h1>
        </div>

        {/* Progress */}
        <div className="flex gap-2 mb-6">
          {steps.map((_, idx) => (
            <div key={idx} className={`flex-1 h-2 rounded-full ${idx + 1 <= step ? 'bg-blue-600' : 'bg-gray-200'}`} />
          ))}
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">{steps[step - 1].title}</h2>
          {steps[step - 1].fields}

          <div className="flex gap-3 mt-6">
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                className="px-6 py-3 border rounded-lg hover:bg-gray-50"
              >
                Quay lai
              </button>
            )}
            {step < steps.length ? (
              <button
                onClick={() => setStep(step + 1)}
                className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
              >
                Tiep theo <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {submitting ? 'Dang xu ly...' : 'Dang ky'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
