import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Cloud, Eye, EyeOff, Check, X, Loader2 } from 'lucide-react';

interface CloudinarySettings {
  cloud_name: string;
  api_key: string;
  has_api_secret: boolean;
}

export default function AdminSettings() {
  const [settings, setSettings] = useState<CloudinarySettings>({
    cloud_name: '',
    api_key: '',
    has_api_secret: false
  });
  const [apiSecret, setApiSecret] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch('/api/admin/settings/cloudinary');
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage('');
    setTestResult(null);
    
    try {
      const payload: any = {
        cloud_name: settings.cloud_name,
        api_key: settings.api_key
      };
      
      if (apiSecret) {
        payload.api_secret = apiSecret;
      }
      
      const response = await fetch('/api/admin/settings/cloudinary', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        setSaveMessage('Настройки сохранены');
        setApiSecret('');
        await loadSettings();
        setTimeout(() => setSaveMessage(''), 3000);
      } else {
        const data = await response.json();
        setSaveMessage(`Ошибка: ${data.error}`);
      }
    } catch (error) {
      setSaveMessage('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    
    try {
      const response = await fetch('/api/admin/settings/cloudinary/test', {
        method: 'POST'
      });
      const data = await response.json();
      setTestResult({
        success: data.success,
        message: data.success ? data.message : data.error
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Ошибка проверки подключения'
      });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cloud className="h-5 w-5" />
            Cloudinary
          </CardTitle>
          <CardDescription>
            Настройки облачного хранилища для изображений товаров
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="cloud_name">Cloud Name</Label>
            <Input
              id="cloud_name"
              value={settings.cloud_name}
              onChange={(e) => setSettings({ ...settings, cloud_name: e.target.value })}
              placeholder="your-cloud-name"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="api_key">API Key</Label>
            <Input
              id="api_key"
              value={settings.api_key}
              onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
              placeholder="123456789012345"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="api_secret">
              API Secret 
              {settings.has_api_secret && (
                <span className="ml-2 text-xs text-green-600">(установлен)</span>
              )}
            </Label>
            <div className="relative">
              <Input
                id="api_secret"
                type={showSecret ? 'text' : 'password'}
                value={apiSecret}
                onChange={(e) => setApiSecret(e.target.value)}
                placeholder={settings.has_api_secret ? '••••••••••••••••' : 'Введите API Secret'}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => setShowSecret(!showSecret)}
              >
                {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Оставьте пустым, чтобы сохранить текущий секрет
            </p>
          </div>
          
          <div className="flex gap-3 pt-4">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Сохранение...
                </>
              ) : (
                'Сохранить'
              )}
            </Button>
            
            <Button variant="outline" onClick={handleTest} disabled={testing}>
              {testing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Проверка...
                </>
              ) : (
                'Проверить подключение'
              )}
            </Button>
          </div>
          
          {saveMessage && (
            <p className={`text-sm ${saveMessage.includes('Ошибка') ? 'text-red-600' : 'text-green-600'}`}>
              {saveMessage}
            </p>
          )}
          
          {testResult && (
            <div className={`flex items-center gap-2 p-3 rounded-md ${
              testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
            }`}>
              {testResult.success ? (
                <Check className="h-4 w-4" />
              ) : (
                <X className="h-4 w-4" />
              )}
              <span className="text-sm">{testResult.message}</span>
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Как получить данные Cloudinary</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>1. Зарегистрируйтесь на <a href="https://cloudinary.com" target="_blank" rel="noopener noreferrer" className="text-primary underline">cloudinary.com</a></p>
          <p>2. Перейдите в Dashboard</p>
          <p>3. Скопируйте Cloud Name, API Key и API Secret</p>
          <p>4. Вставьте их в форму выше и сохраните</p>
        </CardContent>
      </Card>
    </div>
  );
}
