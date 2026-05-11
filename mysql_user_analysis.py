"""
MySQL用户行为分析脚本
User Behavior Analysis with MySQL
适用于电商、APP、网站等用户行为数据分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class MySQLUserBehaviorAnalysis:
    """
    MySQL用户行为分析类
    """

    def __init__(self, host, port, user, password, database):
        """
        初始化数据库连接

        Args:
            host: 数据库主机地址
            port: 端口号
            user: 用户名
            password: 密码
            database: 数据库名
        """
        self.connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
        self.engine = None

    def connect(self):
        """
        连接数据库
        """
        try:
            self.engine = create_engine(self.connection_string)
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ 数据库连接成功!")
            return True
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            return False

    def get_table_info(self):
        """
        获取数据库中所有表的信息
        """
        query = """
        SELECT 
            TABLE_NAME as table_name,
            TABLE_ROWS as row_count,
            DATA_LENGTH / 1024 / 1024 as data_size_mb,
            TABLE_COMMENT as table_comment
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_ROWS DESC
        """
        return pd.read_sql(query, self.engine)

    def execute_query(self, sql):
        """
        执行SQL查询并返回DataFrame
        """
        try:
            df = pd.read_sql(sql, self.engine)
            return df
        except Exception as e:
            print(f"查询执行失败: {e}")
            return None

    def analyze_daily_active_users(self, table_name='user_behavior', date_col='date', user_col='user_id'):
        """
        分析日活跃用户数(DAU)
        """
        sql = f"""
        SELECT 
            {date_col} as date,
            COUNT(DISTINCT {user_col}) as dau,
            COUNT(*) as total_events
        FROM {table_name}
        GROUP BY {date_col}
        ORDER BY {date_col}
        """
        df = self.execute_query(sql)
        if df is not None:
            print("\n" + "="*60)
            print("日活跃用户数分析 (DAU)")
            print("="*60)
            print(df.to_string(index=False))
        return df

    def analyze_user_retention(self, table_name='user_behavior', date_col='date', user_col='user_id'):
        """
        分析用户留存率
        """
        sql = f"""
        WITH first_login AS (
            SELECT 
                {user_col},
                MIN({date_col}) as first_date
            FROM {table_name}
            GROUP BY {user_col}
        ),
        user_dates AS (
            SELECT DISTINCT 
                {user_col}, 
                {date_col}
            FROM {table_name}
        )
        SELECT 
            fl.first_date,
            COUNT(DISTINCT fl.{user_col}) as new_users,
            COUNT(DISTINCT CASE WHEN ud.{date_col} = DATE_ADD(fl.first_date, INTERVAL 1 DAY) 
                THEN fl.{user_col} END) as day1_retention,
            COUNT(DISTINCT CASE WHEN ud.{date_col} = DATE_ADD(fl.first_date, INTERVAL 7 DAY) 
                THEN fl.{user_col} END) as day7_retention,
            COUNT(DISTINCT CASE WHEN ud.{date_col} = DATE_ADD(fl.first_date, INTERVAL 30 DAY) 
                THEN fl.{user_col} END) as day30_retention
        FROM first_login fl
        LEFT JOIN user_dates ud ON fl.{user_col} = ud.{user_col}
        GROUP BY fl.first_date
        ORDER BY fl.first_date
        """
        df = self.execute_query(sql)
        if df is not None:
            df['day1_retention_rate'] = (df['day1_retention'] / df['new_users'] * 100).round(2)
            df['day7_retention_rate'] = (df['day7_retention'] / df['new_users'] * 100).round(2)
            df['day30_retention_rate'] = (df['day30_retention'] / df['new_users'] * 100).round(2)
            print("\n" + "="*60)
            print("用户留存率分析")
            print("="*60)
            print(df.to_string(index=False))
        return df

    def analyze_user_behavior_funnel(self, table_name='user_behavior', 
                                      user_col='user_id', behavior_col='behavior_type'):
        """
        分析用户行为漏斗
        """
        sql = f"""
        SELECT 
            {behavior_col} as behavior,
            COUNT(DISTINCT {user_col}) as user_count
        FROM {table_name}
        GROUP BY {behavior_col}
        ORDER BY user_count DESC
        """
        df = self.execute_query(sql)
        if df is not None and len(df) > 0:
            df['conversion_rate'] = (df['user_count'] / df['user_count'].max() * 100).round(2)
            print("\n" + "="*60)
            print("用户行为漏斗分析")
            print("="*60)
            print(df.to_string(index=False))
        return df

    def analyze_user_segment(self, table_name='user_behavior', 
                              user_col='user_id', behavior_col='behavior_type'):
        """
        用户分群分析 (RFM模型思想)
        """
        sql = f"""
        SELECT 
            {user_col},
            COUNT(*) as total_actions,
            COUNT(DISTINCT DATE(date)) as active_days,
            MAX(date) as last_active,
            DATEDIFF(CURDATE(), MAX(date)) as recency
        FROM {table_name}
        GROUP BY {user_col}
        """
        df = self.execute_query(sql)
        if df is not None:
            df['frequency_score'] = pd.qcut(df['active_days'], 5, labels=[1,2,3,4,5])
            df['recency_score'] = pd.qcut(df['recency'], 5, labels=[5,4,3,2,1])
            df['user_segment'] = df.apply(lambda x: self._get_user_segment(x['recency_score'], x['frequency_score']), axis=1)
            
            segment_summary = df.groupby('user_segment').agg({
                user_col: 'count',
                'total_actions': 'mean',
                'active_days': 'mean'
            }).round(2)
            segment_summary.columns = ['user_count', 'avg_actions', 'avg_active_days']
            
            print("\n" + "="*60)
            print("用户分群分析")
            print("="*60)
            print(segment_summary.to_string())
        return df

    def _get_user_segment(self, recency, frequency):
        """
        根据RFM得分划分用户群体
        """
        r = int(recency)
        f = int(frequency)
        if r >= 4 and f >= 4:
            return "高价值用户"
        elif r >= 4 and f < 4:
            return "新用户"
        elif r < 4 and f >= 4:
            return "流失风险用户"
        else:
            return "低活跃用户"

    def analyze_hourly_distribution(self, table_name='user_behavior', 
                                     datetime_col='datetime', user_col='user_id'):
        """
        分析用户行为时间分布
        """
        sql = f"""
        SELECT 
            HOUR({datetime_col}) as hour,
            COUNT(*) as event_count,
            COUNT(DISTINCT {user_col}) as active_users
        FROM {table_name}
        GROUP BY HOUR({datetime_col})
        ORDER BY hour
        """
        df = self.execute_query(sql)
        if df is not None:
            print("\n" + "="*60)
            print("用户行为时间分布")
            print("="*60)
            print(df.to_string(index=False))
        return df

    def analyze_top_users(self, table_name='user_behavior', user_col='user_id', limit=20):
        """
        分析活跃度最高的用户
        """
        sql = f"""
        SELECT 
            {user_col},
            COUNT(*) as total_events,
            COUNT(DISTINCT DATE(date)) as active_days,
            MIN(date) as first_active,
            MAX(date) as last_active
        FROM {table_name}
        GROUP BY {user_col}
        ORDER BY total_events DESC
        LIMIT {limit}
        """
        df = self.execute_query(sql)
        if df is not None:
            print("\n" + "="*60)
            print(f"Top {limit} 活跃用户")
            print("="*60)
            print(df.to_string(index=False))
        return df

    def plot_analysis(self, df_dict):
        """
        绘制分析图表
        """
        n_plots = len(df_dict)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()

        plot_idx = 0
        for name, df in df_dict.items():
            if df is None or len(df) == 0:
                continue
            
            ax = axes[plot_idx]
            
            if name == 'DAU':
                ax.plot(df['date'], df['dau'], 'b-o', linewidth=2, markersize=4)
                ax.set_title('日活跃用户数(DAU)', fontsize=12)
                ax.set_xlabel('日期')
                ax.set_ylabel('用户数')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True, alpha=0.3)
                
            elif name == '漏斗':
                bars = ax.barh(df['behavior'], df['user_count'], color='steelblue')
                ax.set_title('用户行为漏斗', fontsize=12)
                ax.set_xlabel('用户数')
                for bar, rate in zip(bars, df['conversion_rate']):
                    ax.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2, 
                           f'{rate}%', va='center')
                           
            elif name == '时间分布':
                ax.bar(df['hour'], df['event_count'], color='coral', edgecolor='black')
                ax.set_title('用户行为时间分布', fontsize=12)
                ax.set_xlabel('小时')
                ax.set_ylabel('事件数')
                ax.set_xticks(range(0, 24, 2))
                ax.grid(True, alpha=0.3, axis='y')
                
            elif name == '留存':
                x = range(len(df))
                width = 0.25
                ax.bar([i - width for i in x], df['day1_retention_rate'], width, label='次日留存', color='green')
                ax.bar(x, df['day7_retention_rate'], width, label='7日留存', color='blue')
                ax.bar([i + width for i in x], df['day30_retention_rate'], width, label='30日留存', color='red')
                ax.set_title('用户留存率', fontsize=12)
                ax.set_xlabel('日期')
                ax.set_ylabel('留存率(%)')
                ax.legend()
                ax.tick_params(axis='x', rotation=45)
            
            plot_idx += 1
            if plot_idx >= 4:
                break

        plt.tight_layout()
        plt.savefig('user_behavior_analysis.png', dpi=150, bbox_inches='tight')
        plt.show()
        print("\n图表已保存至: user_behavior_analysis.png")


def create_sample_data_sql():
    """
    生成示例数据表的SQL语句
    """
    sql = """
    -- 创建用户行为表
    CREATE TABLE IF NOT EXISTS user_behavior (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL,
        item_id VARCHAR(50),
        behavior_type VARCHAR(20) COMMENT 'pv/click/cart/buy/fav',
        date DATE,
        datetime DATETIME,
        device VARCHAR(20),
        platform VARCHAR(20)
    );

    -- 创建用户表
    CREATE TABLE IF NOT EXISTS users (
        user_id VARCHAR(50) PRIMARY KEY,
        gender TINYINT COMMENT '0女1男',
        age INT,
        city VARCHAR(50),
        register_date DATE,
        vip_level INT DEFAULT 0
    );

    -- 创建商品表
    CREATE TABLE IF NOT EXISTS items (
        item_id VARCHAR(50) PRIMARY KEY,
        category_id VARCHAR(50),
        brand VARCHAR(100),
        price DECIMAL(10,2)
    );
    """
    return sql


def main():
    """
    主函数
    """
    print("="*70)
    print("MySQL 用户行为分析工具")
    print("User Behavior Analysis Tool")
    print("="*70)

    print("\n请配置数据库连接信息:")
    print("-" * 40)
    
    host = input("数据库主机 (默认localhost): ").strip() or "localhost"
    port = input("端口 (默认3306): ").strip() or "3306"
    user = input("用户名: ").strip()
    password = input("密码: ").strip()
    database = input("数据库名: ").strip()

    analyzer = MySQLUserBehaviorAnalysis(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )

    if not analyzer.connect():
        print("\n连接失败，请检查配置信息")
        return

    print("\n正在获取数据库表信息...")
    tables = analyzer.get_table_info()
    print("\n数据库中的表:")
    print(tables.to_string(index=False))

    print("\n" + "="*70)
    print("请输入要分析的表名 (默认: user_behavior):")
    table_name = input().strip() or "user_behavior"

    print(f"\n开始分析表: {table_name}")
    print("="*70)

    results = {}

    print("\n[1] 分析日活跃用户数...")
    results['DAU'] = analyzer.analyze_daily_active_users(table_name=table_name)

    print("\n[2] 分析用户行为漏斗...")
    results['漏斗'] = analyzer.analyze_user_behavior_funnel(table_name=table_name)

    print("\n[3] 分析用户行为时间分布...")
    results['时间分布'] = analyzer.analyze_hourly_distribution(table_name=table_name)

    print("\n[4] 分析用户留存...")
    results['留存'] = analyzer.analyze_user_retention(table_name=table_name)

    print("\n[5] 分析Top活跃用户...")
    analyzer.analyze_top_users(table_name=table_name)

    print("\n[6] 用户分群分析...")
    analyzer.analyze_user_segment(table_name=table_name)

    print("\n正在生成可视化图表...")
    analyzer.plot_analysis(results)

    print("\n" + "="*70)
    print("分析完成!")
    print("="*70)

    return analyzer


if __name__ == "__main__":
    analyzer = main()
