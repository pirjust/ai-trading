"""
深度学习模型架构
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np

class AttentionMechanism(nn.Module):
    """注意力机制模块"""
    
    def __init__(self, hidden_size: int):
        super(AttentionMechanism, self).__init__()
        self.hidden_size = hidden_size
        self.attention_weights = nn.Linear(hidden_size, 1)
    
    def forward(self, hidden_states: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """前向传播"""
        # 计算注意力权重
        attention_scores = self.attention_weights(hidden_states).squeeze(-1)
        attention_weights = F.softmax(attention_scores, dim=1)
        
        # 计算加权和
        context_vector = torch.sum(hidden_states * attention_weights.unsqueeze(-1), dim=1)
        
        return context_vector, attention_weights

class MultiHeadAttention(nn.Module):
    """多头注意力机制"""
    
    def __init__(self, hidden_size: int, num_heads: int = 8):
        super(MultiHeadAttention, self).__init__()
        assert hidden_size % num_heads == 0
        
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads
        
        # 查询、键、值线性变换
        self.query = nn.Linear(hidden_size, hidden_size)
        self.key = nn.Linear(hidden_size, hidden_size)
        self.value = nn.Linear(hidden_size, hidden_size)
        
        # 输出线性变换
        self.output = nn.Linear(hidden_size, hidden_size)
        
        # 缩放因子
        self.scale = torch.sqrt(torch.FloatTensor([self.head_dim]))
    
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor, 
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """前向传播"""
        batch_size = query.shape[0]
        
        # 线性变换
        Q = self.query(query).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.key(key).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.value(value).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算注意力分数
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale.to(query.device)
        
        # 应用掩码（如果有）
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        # 计算注意力权重
        attention_weights = F.softmax(scores, dim=-1)
        
        # 应用注意力权重
        attention_output = torch.matmul(attention_weights, V)
        
        # 拼接多头输出
        attention_output = attention_output.transpose(1, 2).contiguous().view(
            batch_size, -1, self.hidden_size)
        
        # 输出线性变换
        output = self.output(attention_output)
        
        return output

class TransformerEncoderLayer(nn.Module):
    """Transformer编码器层"""
    
    def __init__(self, hidden_size: int, num_heads: int = 8, ff_size: int = 2048, 
                 dropout: float = 0.1):
        super(TransformerEncoderLayer, self).__init__()
        
        self.self_attention = MultiHeadAttention(hidden_size, num_heads)
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_size, ff_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_size, hidden_size),
            nn.Dropout(dropout)
        )
        
        self.norm1 = nn.LayerNorm(hidden_size)
        self.norm2 = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """前向传播"""
        # 自注意力子层
        attention_output = self.self_attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attention_output))
        
        # 前馈子层
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        
        return x

class TimeSeriesTransformer(nn.Module):
    """时间序列Transformer模型"""
    
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 6, 
                 num_heads: int = 8, ff_size: int = 512, dropout: float = 0.1, 
                 output_size: int = 3):
        super(TimeSeriesTransformer, self).__init__()
        
        self.input_projection = nn.Linear(input_size, hidden_size)
        self.positional_encoding = PositionalEncoding(hidden_size, dropout)
        
        # Transformer编码器层
        self.encoder_layers = nn.ModuleList([
            TransformerEncoderLayer(hidden_size, num_heads, ff_size, dropout)
            for _ in range(num_layers)
        ])
        
        # 输出层
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size)
        )
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """前向传播"""
        # 输入投影
        x = self.input_projection(x)
        
        # 位置编码
        x = self.positional_encoding(x)
        
        # Transformer编码器
        for layer in self.encoder_layers:
            x = layer(x, mask)
        
        # 取最后一个时间步
        x = x[:, -1, :]
        
        # 输出层
        output = self.output_layer(x)
        
        return output

class PositionalEncoding(nn.Module):
    """位置编码"""
    
    def __init__(self, hidden_size: int, dropout: float = 0.1, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # 创建位置编码矩阵
        pe = torch.zeros(max_len, hidden_size)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, hidden_size, 2).float() * 
                           (-np.log(10000.0) / hidden_size))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        x = x + self.pe[:x.size(1), :].transpose(0, 1)
        return self.dropout(x)

class CNNLSTMHybrid(nn.Module):
    """CNN-LSTM混合模型"""
    
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, 
                 kernel_size: int = 3, output_size: int = 3):
        super(CNNLSTMHybrid, self).__init__()
        
        # CNN部分 - 提取局部特征
        self.conv1d = nn.Sequential(
            nn.Conv1d(input_size, hidden_size, kernel_size, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(hidden_size, hidden_size, kernel_size, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )
        
        # LSTM部分 - 处理时序依赖
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers, 
                           batch_first=True, dropout=0.2)
        
        # 注意力机制
        self.attention = AttentionMechanism(hidden_size)
        
        # 输出层
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size // 2, output_size)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        # 转置输入以适应CNN
        x = x.transpose(1, 2)
        
        # CNN特征提取
        cnn_features = self.conv1d(x)
        
        # 转回以适应LSTM
        cnn_features = cnn_features.transpose(1, 2)
        
        # LSTM时序处理
        lstm_out, (hidden, cell) = self.lstm(cnn_features)
        
        # 注意力机制
        context_vector, attention_weights = self.attention(lstm_out)
        
        # 输出层
        output = self.output_layer(context_vector)
        
        return output

class VariationalAutoencoder(nn.Module):
    """变分自编码器 - 用于特征学习和异常检测"""
    
    def __init__(self, input_size: int, hidden_size: int = 32, latent_size: int = 16):
        super(VariationalAutoencoder, self).__init__()
        
        # 编码器
        self.encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU()
        )
        
        # 均值和对数方差
        self.fc_mu = nn.Linear(hidden_size // 2, latent_size)
        self.fc_logvar = nn.Linear(hidden_size // 2, latent_size)
        
        # 解码器
        self.decoder = nn.Sequential(
            nn.Linear(latent_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, input_size)
        )
    
    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """编码"""
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar
    
    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """重参数化技巧"""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """解码"""
        return self.decoder(z)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """前向传播"""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        reconstructed = self.decode(z)
        return reconstructed, mu, logvar

class EnsembleModel:
    """模型集成 - 结合多个模型的预测结果"""
    
    def __init__(self, models: List[nn.Module], weights: Optional[List[float]] = None):
        self.models = models
        self.weights = weights if weights else [1.0 / len(models)] * len(models)
        
        # 确保权重总和为1
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]
    
    def predict(self, x: torch.Tensor) -> torch.Tensor:
        """集成预测"""
        predictions = []
        
        for model in self.models:
            model.eval()
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)
        
        # 加权平均
        weighted_predictions = torch.zeros_like(predictions[0])
        for i, pred in enumerate(predictions):
            weighted_predictions += self.weights[i] * pred
        
        return weighted_predictions
    
    def add_model(self, model: nn.Module, weight: float = None):
        """添加新模型"""
        self.models.append(model)
        
        if weight is None:
            # 自动调整权重
            new_total = len(self.models)
            self.weights = [1.0 / new_total] * new_total
        else:
            self.weights.append(weight)
            # 重新归一化权重
            total_weight = sum(self.weights)
            self.weights = [w / total_weight for w in self.weights]

class ModelFactory:
    """模型工厂 - 创建和管理各种深度学习模型"""
    
    @staticmethod
    def create_model(model_type: str, input_size: int, **kwargs) -> nn.Module:
        """创建模型"""
        if model_type == 'transformer':
            return TimeSeriesTransformer(
                input_size=input_size,
                hidden_size=kwargs.get('hidden_size', 128),
                num_layers=kwargs.get('num_layers', 6),
                num_heads=kwargs.get('num_heads', 8),
                output_size=kwargs.get('output_size', 3)
            )
        elif model_type == 'cnn_lstm':
            return CNNLSTMHybrid(
                input_size=input_size,
                hidden_size=kwargs.get('hidden_size', 64),
                num_layers=kwargs.get('num_layers', 2),
                output_size=kwargs.get('output_size', 3)
            )
        elif model_type == 'vae':
            return VariationalAutoencoder(
                input_size=input_size,
                hidden_size=kwargs.get('hidden_size', 32),
                latent_size=kwargs.get('latent_size', 16)
            )
        elif model_type == 'lstm':
            return nn.LSTM(
                input_size=input_size,
                hidden_size=kwargs.get('hidden_size', 64),
                num_layers=kwargs.get('num_layers', 2),
                batch_first=True,
                dropout=kwargs.get('dropout', 0.2)
            )
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
    
    @staticmethod
    def create_ensemble(models_config: List[Dict]) -> EnsembleModel:
        """创建集成模型"""
        models = []
        weights = []
        
        for config in models_config:
            model = ModelFactory.create_model(**config)
            models.append(model)
            weights.append(config.get('weight', 1.0))
        
        return EnsembleModel(models, weights)

# 损失函数定义
class CustomLossFunctions:
    """自定义损失函数"""
    
    @staticmethod
    def sharpe_ratio_loss(returns: torch.Tensor, risk_free_rate: float = 0.0) -> torch.Tensor:
        """夏普比率损失（最大化夏普比率）"""
        excess_returns = returns - risk_free_rate
        mean_return = torch.mean(excess_returns)
        std_return = torch.std(excess_returns)
        
        # 避免除零
        sharpe_ratio = mean_return / (std_return + 1e-8)
        
        # 最大化夏普比率 = 最小化负夏普比率
        return -sharpe_ratio
    
    @staticmethod
    def maximum_drawdown_loss(prices: torch.Tensor) -> torch.Tensor:
        """最大回撤损失（最小化最大回撤）"""
        # 计算累积最大值
        cumulative_max = torch.cummax(prices, dim=0)[0]
        
        # 计算回撤
        drawdown = (cumulative_max - prices) / cumulative_max
        
        # 最大回撤
        max_drawdown = torch.max(drawdown)
        
        return max_drawdown
    
    @staticmethod
    def volatility_penalty_loss(returns: torch.Tensor, target_volatility: float = 0.1) -> torch.Tensor:
        """波动率惩罚损失"""
        actual_volatility = torch.std(returns)
        volatility_diff = torch.abs(actual_volatility - target_volatility)
        return volatility_diff
    
    @staticmethod
    def vae_loss(reconstructed_x: torch.Tensor, x: torch.Tensor, mu: torch.Tensor, 
                logvar: torch.Tensor, beta: float = 1.0) -> torch.Tensor:
        """VAE损失函数"""
        # 重构损失
        reconstruction_loss = F.mse_loss(reconstructed_x, x, reduction='sum')
        
        # KL散度
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        
        return reconstruction_loss + beta * kl_loss