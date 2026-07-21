<?php

declare(strict_types=1);

final class OrderController
{
    public function __construct(private OrderService $orderService)
    {
    }

    /** 建立訂單。 */
    public function create(array $input): array
    {
        return $this->orderService->create($input);
    }
}
