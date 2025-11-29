import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { AlertCircle } from 'lucide-react';

interface RegisterProps {
  onLoginClick: () => void;
  onSuccess: () => void;
}

const validateEmail = (email: string): { valid: boolean; error?: string } => {
  if (!email) return { valid: false, error: 'Email обязателен' };
  const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!emailPattern.test(email)) {
    return { valid: false, error: 'Неверный формат email' };
  }
  return { valid: true };
};

const validatePhone = (phone: string): { valid: boolean; error?: string } => {
  if (!phone) return { valid: true }; // Phone is optional
  const cleaned = phone.replace(/[^\d+]/g, '');
  const digits = cleaned.startsWith('+') ? cleaned.slice(1) : cleaned;
  if (digits.length < 7 || digits.length > 15) {
    return { valid: false, error: 'Телефон должен содержать от 7 до 15 цифр' };
  }
  if (!/^\d+$/.test(digits)) {
    return { valid: false, error: 'Телефон должен содержать только цифры' };
  }
  return { valid: true };
};

export default function Register({ onLoginClick, onSuccess }: RegisterProps) {
  const { register } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    telegram_username: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const clearError = (field: string) => {
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    
    // Validate email
    const emailValidation = validateEmail(formData.email);
    if (!emailValidation.valid) {
      newErrors.email = emailValidation.error!;
    }
    
    // Validate phone
    const phoneValidation = validatePhone(formData.phone);
    if (!phoneValidation.valid) {
      newErrors.phone = phoneValidation.error!;
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
    }

    if (formData.password.length < 6) {
      newErrors.password = 'Пароль должен быть не менее 6 символов';
    }

    if (!formData.telegram_username) {
      newErrors.telegram_username = 'Telegram username обязателен';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      toast({
        title: 'Ошибка',
        description: Object.values(newErrors)[0],
        variant: 'destructive',
      });
      return;
    }
    
    setErrors({});
    setLoading(true);
    const result = await register({
      email: formData.email,
      password: formData.password,
      first_name: formData.first_name,
      last_name: formData.last_name,
      phone: formData.phone,
      telegram_username: formData.telegram_username,
    });

    setLoading(false);

    if (result.success) {
      toast({
        title: 'Успешно',
        description: 'Регистрация выполнена',
      });
      onSuccess();
    } else {
      toast({
        title: 'Ошибка',
        description: result.error || 'Ошибка регистрации',
        variant: 'destructive',
      });
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    clearError(name);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md">
        <div className="bg-card rounded-2xl shadow-lg p-6 sm:p-8 border border-card-border">
          <h1 className="text-2xl font-bold text-center mb-6">Регистрация</h1>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Имя *</label>
              <Input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                required
                placeholder="Введите имя"
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">Фамилия</label>
              <Input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                placeholder="Введите фамилию"
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">Email *</label>
              <Input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="example@email.com"
                className={`w-full ${errors.email ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
              />
              {errors.email && (
                <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.email}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">Телефон</label>
              <Input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+7 (999) 123-45-67"
                className={`w-full ${errors.phone ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
              />
              {errors.phone && (
                <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.phone}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">Telegram username *</label>
              <Input
                type="text"
                name="telegram_username"
                value={formData.telegram_username}
                onChange={handleChange}
                required
                placeholder="@username"
                className={`w-full ${errors.telegram_username ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
              />
              {errors.telegram_username && (
                <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.telegram_username}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">Пароль *</label>
              <Input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="Минимум 6 символов"
                className={`w-full ${errors.password ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
              />
              {errors.password && (
                <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.password}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5">Подтвердите пароль *</label>
              <Input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                placeholder="Повторите пароль"
                className={`w-full ${errors.confirmPassword ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
              />
              {errors.confirmPassword && (
                <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  {errors.confirmPassword}
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? 'Регистрация...' : 'Зарегистрироваться'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Уже есть аккаунт?{' '}
              <button
                onClick={onLoginClick}
                className="text-primary font-medium hover:underline"
              >
                Войти
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
