import { useState } from 'react';
import { Upload, Download, FileSpreadsheet, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

interface UploadResult {
  success: boolean;
  message: string;
  details?: string;
}

export default function BulkUploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setResult(null);
      
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        const lines = text.split('\n');
        const headers = lines[0].split(',');
        const data = lines.slice(1, 6).map(line => {
          const values = line.split(',');
          const obj: any = {};
          headers.forEach((header, index) => {
            obj[header.trim()] = values[index]?.trim() || '';
          });
          return obj;
        });
        setPreviewData(data);
      };
      reader.readAsText(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const res = await api.uploadFile(file, 'product');
      setResult({
        success: true,
        message: 'Upload thành công!',
        details: `Đã thêm ${res.count || '?'} sản phẩm vào kho`,
      });
    } catch (err: any) {
      setResult({
        success: false,
        message: 'Upload thất bại',
        details: err.message || 'File không đúng định dạng',
      });
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const template = `name,price,stock,unit,barcode,brand,shelf_location,category
Panadol Extra 500mg,35000,100,hộp,8945123456789,Pfizer,A1,Thuốc giảm đau
Vitamin C 1000mg,45000,50,vỉ,8945123456790,Blackmores,B2,Vitamin
Khẩu trang y tế,15000,200,hộp,8945123456791,3M,C1,Thiết bị y tế`;
    
    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'template_san_pham.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 rounded-full">
          <XCircle className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold">Bulk Upload Sản phẩm</h1>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-blue-900">Hướng dẫn upload</h3>
            <ul className="text-sm text-blue-800 mt-2 space-y-1">
              <li>• Tải xuống template CSV và điền thông tin sản phẩm</li>
              <li>• File phải có định dạng CSV với các cột: name, price, stock, unit, barcode, brand, shelf_location, category</li>
              <li>• Mỗi dòng tương ứng với 1 sản phẩm</li>
              <li>• Hệ thống sẽ tự động validate và báo lỗi nếu có</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="w-8 h-8 text-green-600" />
            <div>
              <h3 className="font-semibold">Template CSV</h3>
              <p className="text-sm text-gray-500">Tải xuống template chuẩn để điền thông tin</p>
            </div>
          </div>
          <button onClick={downloadTemplate} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2">
            <Download className="w-4 h-4" /> Tải template
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition cursor-pointer">
          <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFileSelect} className="hidden" id="file-upload" />
          <label htmlFor="file-upload" className="cursor-pointer">
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-2">Kéo thả file vào đây hoặc click để chọn</p>
            <p className="text-sm text-gray-400">Hỗ trợ: CSV, Excel (.xlsx, .xls)</p>
          </label>
        </div>

        {file && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
              </div>
              <button onClick={() => { setFile(null); setPreviewData([]); setResult(null); }} className="p-2 hover:bg-gray-200 rounded">
                <XCircle className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>
        )}
      </div>

      {previewData.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-4 mb-6">
          <h3 className="font-semibold mb-4">Xem trước dữ liệu (5 dòng đầu)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  {Object.keys(previewData[0]).map((key) => <th key={key} className="text-left py-2 px-3 font-medium text-gray-600">{key}</th>)}
                </tr>
              </thead>
              <tbody>
                {previewData.map((row, idx) => (
                  <tr key={idx} className="border-b">
                    {Object.values(row).map((value, cellIdx) => <td key={cellIdx} className="py-2 px-3 text-gray-700">{value as string}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {result && (
        <div className={`rounded-xl p-4 mb-6 ${result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-start gap-3">
            {result.success ? <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" /> : <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />}
            <div>
              <p className={`font-semibold ${result.success ? 'text-green-900' : 'text-red-900'}`}>{result.message}</p>
              {result.details && <p className={`text-sm mt-1 ${result.success ? 'text-green-700' : 'text-red-700'}`}>{result.details}</p>}
            </div>
          </div>
        </div>
      )}

      {file && (
        <button onClick={handleUpload} disabled={uploading} className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50">
          {uploading ? 'Đang upload...' : 'Upload sản phẩm'}
        </button>
      )}
    </div>
  );
}
