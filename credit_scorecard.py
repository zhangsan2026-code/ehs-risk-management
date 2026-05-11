"""
银行信用评分卡模型
Bank Credit Scorecard Model
基于逻辑回归的评分卡模型，用于个人信贷风险评估
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class CreditScorecard:
    """
    信用评分卡模型类
    实现标准的评分卡模型开发流程
    """

    def __init__(self, target_rate=0.15, score_base=600, odds_base=1/20, PDO=50):
        """
        初始化评分卡参数

        Args:
            target_rate: 目标好坏比（坏人/好人比例），默认为0.15
            score_base: 基准评分，默认为600
            odds_base: 基准Odds（好坏比），默认为1:20
            PDO: 翻倍比率，表示Odds增加一倍时评分增加的点数
        """
        self.target_rate = target_rate
        self.score_base = score_base
        self.odds_base = odds_base
        self.PDO = PDO
        self.woe_dict = {}
        self.bin_edges = {}
        self.model = None
        self.features = None

    def generate_sample_data(self, n_samples=10000, seed=42):
        """
        生成模拟银行信贷数据

        Args:
            n_samples: 样本数量
            seed: 随机种子

        Returns:
            DataFrame: 包含特征和目标变量的数据集
        """
        np.random.seed(seed)

        data = pd.DataFrame()

        data['age'] = np.random.normal(45, 12, n_samples).clip(22, 70)
        data['income'] = np.random.lognormal(11, 0.6, n_samples)
        data['loan_amount'] = np.random.lognormal(10.5, 0.8, n_samples)
        data['loan_term'] = np.random.choice([12, 24, 36, 48, 60], n_samples, p=[0.1, 0.2, 0.35, 0.25, 0.1])
        data['credit_history_years'] = np.random.exponential(8, n_samples).clip(0, 30)
        data['debt_ratio'] = np.random.beta(2, 5, n_samples)
        data['employment_years'] = np.random.exponential(5, n_samples).clip(0, 40)
        data['has_other_loans'] = np.random.binomial(1, 0.3, n_samples)
        data['payment punctuality'] = np.random.beta(8, 2, n_samples)
        data['education_level'] = np.random.choice([1, 2, 3, 4], n_samples, p=[0.2, 0.4, 0.3, 0.1])

        probability = (
            0.3 +
            0.02 * (data['age'] - 45) / 10 +
            -0.3 * np.log(data['income'] / 50000) +
            0.2 * np.log(data['loan_amount'] / 30000) +
            0.15 * (data['loan_term'] - 36) / 12 +
            -0.4 * data['credit_history_years'] / 10 +
            0.5 * data['debt_ratio'] +
            -0.1 * data['employment_years'] / 10 +
            0.3 * data['has_other_loans'] +
            -0.3 * data['payment punctuality'] +
            -0.1 * (data['education_level'] - 2)
        )
        probability = 1 / (1 + np.exp(-probability))
        probability = probability.clip(0.02, 0.85)

        data['target'] = np.random.binomial(1, probability)

        return data

    def calculate_woe_iv(self, df, feature, target, bins=5):
        """
        计算WoE(证据权重)和IV(信息价值)

        WoE = ln(坏客户比例 / 好客户比例)
        IV = sum(坏客户比例 - 好客户比例) * WoE
        """
        df_temp = df[[feature, target]].copy()
        df_temp['bin'] = pd.qcut(df_temp[feature], q=bins, duplicates='drop')

        grouped = df_temp.groupby('bin')[target].agg(['sum', 'count'])
        grouped.columns = ['bad', 'total']
        grouped['good'] = grouped['total'] - grouped['bad']

        total_bad = grouped['bad'].sum()
        total_good = grouped['good'].sum()

        grouped['bad_pct'] = grouped['bad'] / total_bad
        grouped['good_pct'] = grouped['good'] / total_good

        grouped['bad_pct'] = grouped['bad_pct'].replace(0, 0.0001)
        grouped['good_pct'] = grouped['good_pct'].replace(0, 0.0001)

        grouped['woe'] = np.log(grouped['bad_pct'] / grouped['good_pct'])
        grouped['iv'] = (grouped['bad_pct'] - grouped['good_pct']) * grouped['woe']

        iv_total = grouped['iv'].sum()

        woe_dict = grouped['woe'].to_dict()
        bin_edges = {}

        for bin_range in grouped.index:
            bin_edges[bin_range] = bin_range

        return woe_dict, iv_total, bin_edges

    def preprocess_data(self, df, target_col='target'):
        """
        数据预处理和特征分箱

        Returns:
            DataFrame: WoE转换后的特征数据
        """
        target = df[target_col]
        features_df = df.drop(columns=[target_col])

        woe_df = pd.DataFrame()

        for col in features_df.columns:
            if col == 'target':
                continue

            if features_df[col].nunique() <= 5:
                bins = features_df[col].nunique()
            else:
                bins = 5

            woe_dict, iv, bin_edges = self.calculate_woe_iv(
                df, col, target_col, bins=bins
            )

            self.woe_dict[col] = woe_dict
            self.bin_edges[col] = bin_edges

            woe_col = features_df[col].apply(
                lambda x: self._get_woe_value(col, x, woe_dict, bin_edges)
            )
            woe_df[col] = woe_col

        self.features = woe_df.columns.tolist()

        return woe_df, target

    def _get_woe_value(self, feature, value, woe_dict, bin_edges):
        """
        根据特征值获取对应的WoE值
        """
        for bin_range, woe_value in woe_dict.items():
            if value in bin_range:
                return woe_value
        return 0

    def fit(self, X, y):
        """
        训练逻辑回归模型
        """
        self.model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            solver='lbfgs'
        )
        self.model.fit(X, y)

    def predict_proba(self, X):
        """
        预测违约概率
        """
        return self.model.predict_proba(X)[:, 1]

    def calculate_score(self, probability):
        """
        将概率转换为评分卡分数

        Score = A - B * ln(odds)
        其中 odds = P(bad) / P(good)
        """
        odds = probability / (1 - probability)
        A = self.score_base + self.PDO * np.log(self.odds_base)
        B = self.PDO / np.log(2)
        score = A - B * np.log(odds)
        return score

    def evaluate_model(self, y_true, y_pred_proba):
        """
        评估模型性能

        计算AUC、KS值、Gini系数等指标
        """
        auc = roc_auc_score(y_true, y_pred_proba)

        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        ks = max(tpr - fpr)

        gini = 2 * auc - 1

        scores = self.calculate_score(y_pred_proba)

        return {
            'AUC': auc,
            'KS': ks,
            'Gini': gini,
            'FPR': fpr,
            'TPR': tpr,
            'Scores': scores
        }

    def get_scorecard_table(self):
        """
        生成标准评分卡表格
        """
        if self.model is None:
            print("模型尚未训练，请先调用fit方法")
            return None

        coefficients = self.model.coef_[0]
        intercept = self.model.intercept_[0]

        A = self.score_base + self.PDO * np.log(self.odds_base)
        B = self.PDO / np.log(2)

        base_score = A - B * intercept

        scorecard = []

        for i, feature in enumerate(self.features):
            coef = coefficients[i]
            woe_dict = self.woe_dict[feature]

            for bin_range, woe_value in woe_dict.items():
                score_contribution = -B * coef * woe_value
                scorecard.append({
                    '特征': feature,
                    '分箱': str(bin_range),
                    'WoE': round(woe_value, 4),
                    '得分': round(score_contribution, 1)
                })

        scorecard_df = pd.DataFrame(scorecard)

        print("\n" + "="*80)
        print("银行信用评分卡")
        print("="*80)
        print(f"\n基准分: {round(base_score, 0)}")
        print(f"基准Odds: 1:{int(1/self.odds_base)}")
        print(f"PDO: {self.PDO}")
        print("\n" + "-"*80)
        print("分箱得分表:")
        print("-"*80)

        return scorecard_df, base_score

    def plot_model_performance(self, eval_results):
        """
        绘制模型评估图表
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        ax1 = axes[0, 0]
        fpr = eval_results['FPR']
        tpr = eval_results['TPR']
        auc = eval_results['AUC']
        ax1.plot(fpr, tpr, 'b-', linewidth=2, label=f'ROC Curve (AUC = {auc:.4f})')
        ax1.plot([0, 1], [0, 1], 'r--', linewidth=1, label='Random')
        ax1.set_xlabel('False Positive Rate', fontsize=12)
        ax1.set_ylabel('True Positive Rate', fontsize=12)
        ax1.set_title('ROC Curve', fontsize=14)
        ax1.legend(loc='lower right')
        ax1.grid(True, alpha=0.3)

        ax2 = axes[0, 1]
        scores = eval_results['Scores']
        ax2.hist(scores[eval_results.get('y_true', 0) == 0], bins=50, alpha=0.6,
                label='Good Customer', color='green', density=True)
        ax2.hist(scores[eval_results.get('y_true', 0) == 1], bins=50, alpha=0.6,
                label='Bad Customer', color='red', density=True)
        ax2.set_xlabel('Score', fontsize=12)
        ax2.set_ylabel('Density', fontsize=12)
        ax2.set_title('Score Distribution', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        ax3 = axes[1, 0]
        ks_value = eval_results['KS']
        tpr_ks = eval_results['TPR']
        fpr_ks = eval_results['FPR']
        ax3.plot(thresholds := np.linspace(0, 1, 100),
                [np.interp(t, fpr_ks, tpr_ks) for t in thresholds],
                'b-', label='TPR', linewidth=2)
        ax3.plot(thresholds,
                [np.interp(t, fpr_ks, tpr_ks) - t for t in thresholds],
                'r-', label='KS Curve', linewidth=2)
        ax3.axhline(y=ks_value, color='g', linestyle='--', label=f'KS = {ks_value:.4f}')
        ax3.set_xlabel('Threshold', fontsize=12)
        ax3.set_ylabel('Value', fontsize=12)
        ax3.set_title('KS Statistics', fontsize=14)
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        ax4 = axes[1, 1]
        metrics = ['AUC', 'KS', 'Gini']
        values = [auc := eval_results['AUC'],
                 eval_results['KS'],
                 eval_results['Gini']]
        colors = ['#2E86AB', '#A23B72', '#F18F01']
        bars = ax4.bar(metrics, values, color=colors, edgecolor='black', linewidth=1.5)
        ax4.set_ylabel('Value', fontsize=12)
        ax4.set_title('Model Performance Metrics', fontsize=14)
        ax4.set_ylim(0, 1)
        for bar, val in zip(bars, values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{val:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig('scorecard_performance.png', dpi=150, bbox_inches='tight')
        plt.show()

        print("\n图表已保存至: scorecard_performance.png")


def main():
    """
    主函数：演示评分卡模型的完整开发流程
    """
    print("="*80)
    print("银行信用评分卡模型开发演示")
    print("Bank Credit Scorecard Model Development Demo")
    print("="*80)

    model = CreditScorecard(target_rate=0.15, score_base=600, odds_base=1/20, PDO=50)

    print("\n[1] 生成模拟信贷数据...")
    data = model.generate_sample_data(n_samples=10000, seed=42)

    print(f"    数据集大小: {data.shape[0]} 条记录, {data.shape[1]} 个字段")
    print(f"    目标变量分布: 坏客户 {data['target'].sum()} ({data['target'].mean()*100:.2f}%)")
    print(f"                好客户 {len(data) - data['target'].sum()} ({(1-data['target'].mean())*100:.2f}%)")

    print("\n[2] 数据预处理 - 计算WoE和IV值...")
    woe_features, target = model.preprocess_data(data)

    print("\n    各特征IV值（信息价值）:")
    print("    IV < 0.02: 无预测能力 | 0.02-0.1: 弱预测能力")
    print("    0.1-0.3: 中等预测能力 | 0.3-0.5: 强预测能力 | > 0.5: 极强")

    print("\n[3] 划分训练集和测试集...")
    X_train, X_test, y_train, y_test = train_test_split(
        woe_features, target, test_size=0.3, random_state=42, stratify=target
    )
    print(f"    训练集: {len(X_train)} 条 | 测试集: {len(X_test)} 条")

    print("\n[4] 训练逻辑回归模型...")
    model.fit(X_train, y_train)
    print("    模型训练完成!")

    print("\n[5] 模型评估...")
    y_pred_proba_train = model.predict_proba(X_train)
    y_pred_proba_test = model.predict_proba(X_test)

    eval_train = model.evaluate_model(y_train.values, y_pred_proba_train)
    eval_test = model.evaluate_model(y_test.values, y_pred_proba_test)

    print("\n    训练集指标:")
    print(f"    AUC: {eval_train['AUC']:.4f}")
    print(f"    KS:  {eval_train['KS']:.4f}")
    print(f"    Gini: {eval_train['Gini']:.4f}")

    print("\n    测试集指标:")
    print(f"    AUC: {eval_test['AUC']:.4f}")
    print(f"    KS:  {eval_test['KS']:.4f}")
    print(f"    Gini: {eval_test['Gini']:.4f}")

    print("\n[6] 生成评分卡...")
    scorecard_df, base_score = model.get_scorecard_table()
    print(scorecard_df.to_string(index=False))

    print("\n    评分卡使用说明:")
    print("    • 根据客户各项指标找到对应分箱")
    print("    • 将所有分箱得分相加，再加上基准分")
    print("    • 分数越高，客户信用越好，违约风险越低")

    print("\n[7] 风险等级划分示例:")
    print("    分数范围        风险等级    建议策略")
    print("    650以上        极低风险    优先授信，利率优惠")
    print("    550-650        低风险      正常授信，标准利率")
    print("    450-550        中等风险    审慎授信，利率上浮")
    print("    350-450        高风险      限制授信，严格监控")
    print("    350以下        极高风险    拒绝授信")

    eval_test['y_true'] = y_test.values
    print("\n[8] 生成模型评估图表...")
    model.plot_model_performance(eval_test)

    print("\n" + "="*80)
    print("评分卡模型开发演示完成!")
    print("="*80)

    return model, data


if __name__ == "__main__":
    model, data = main()