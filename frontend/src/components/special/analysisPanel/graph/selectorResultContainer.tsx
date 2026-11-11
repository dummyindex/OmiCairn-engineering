import { Space, Tag, Button } from 'antd';

const SelectorResultContainer = (props: any) => {
    const { value, onEdit, valueRange } = props;
    const showedValue = value ? value.slice(0, 8) : [];
    return (
        <Space size={[0, 8]} wrap>
            {showedValue.map((item: string) => {
                return (
                    <Tag color="blue" key={item}>
                        {item}
                    </Tag>
                );
            })}
            <Button type="primary">Edit</Button>
        </Space>
    );
};

export default SelectorResultContainer;